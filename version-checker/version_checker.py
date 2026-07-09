#!/usr/bin/env python3
"""
ClamAV version checker (ACPENG-2944).

Scheduled automation that reconciles the ClamAV version we *deploy* against what
Alpine can actually package and what ClamAV releases upstream, then raises a
Jira ticket when there is something a human can action.

The "current" version is the version actually deployed, read from the private
`clamav-deploy` GitLab repo's per-environment values files (`values/<env>.yaml`,
keys `clamav.version` / `clamavHTTP.version` / `clamavMirror.version`). That
value is a `clamav-http` git tag (e.g. "v0.5.5"); the checker resolves it to the
ClamAV/Alpine pins by reading `clamav/Dockerfile` + `clamav-mirror/Dockerfile`
from `clamav-http` *at that tag*. This reflects what is deployed, not the tip of
master. When environments/components diverge, the checker reasons about the
lowest (most-behind) version and flags the drift.

Because ClamAV reaches our image *through* Alpine (`apk add clamav`), three
version numbers have to be reconciled, not one:

  1. Deployed         - the tag pinned in clamav-deploy -> its Dockerfile pins.
  2. Alpine-reachable - the newest `clamav` package Alpine offers for our
                        branch, newer stable branches, and edge (APKINDEX).
  3. Upstream         - the newest ClamAV release + EOL dates (endoflife.date).

Decision rules (see evaluate()):
  R1  in-branch bump      -> ticket   (our branch has clamav > deployed)
  R2  base bump           -> ticket   (a newer stable branch offers clamav we
                                        can't reach in-branch)
  R4  ClamAV near EOL     -> ticket   (deployed series' eol within WARN_DAYS)
  R5  Alpine base near EOL-> ticket   (our Alpine branch eol within WARN_DAYS)
  R3  upstream ahead      -> SIGNAL   (upstream > best Alpine-reachable). Logged
                                        only - nothing is actionable until Alpine
                                        packages it, at which point R1/R2 fire.

Usage:
    python3 version_checker.py --dry-run     # print findings, no Jira calls
    python3 version_checker.py               # create/refresh Jira tickets

Requires:
    export GITLAB_TOKEN="read-only-PAT"      # always (reads clamav-deploy)
    export JIRA_API_TOKEN="your-PAT"         # only when creating tickets
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
import tarfile
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

import requests
import yaml

# --- Jira -------------------------------------------------------------------
JIRA_URL = "https://collaboration.homeoffice.gov.uk/jira"
JIRA_PROJECT = "ACPENG"
JIRA_EPIC_FIELD = "customfield_10006"
# ACP07: Cloud Security epic (https://collaboration.homeoffice.gov.uk/jira/browse/ACPENG-2598).
JIRA_EPIC_KEY = "ACPENG-2598"
# Stable label used to find/refresh our own tickets instead of duplicating.
DEDUP_LABEL = "clamav-version-check"

# --- Deployed version source (clamav-deploy, private GitLab) ----------------
GITLAB_BASE = "https://gitlab.digital.homeoffice.gov.uk"
GITLAB_API = f"{GITLAB_BASE}/api/v4"
CLAMAV_DEPLOY_PROJECT = "acp/clamav-deploy"
VALUES_PATH = "values"
DEPLOY_REF = "master"
# Keys in each values file that pin a clamav-http tag (e.g. "v0.5.5").
VERSION_KEYS = ("clamav", "clamavHTTP", "clamavMirror")

# --- Shipped pins (clamav-http Dockerfiles, resolved at the deployed tag) ---
CLAMAV_HTTP_RAW = "https://raw.githubusercontent.com/UKHomeOffice/clamav-http"
CLAMAV_DOCKERFILES = ("clamav/Dockerfile", "clamav-mirror/Dockerfile")

# --- Data sources -----------------------------------------------------------
CLAMAV_EOL_API = "https://endoflife.date/api/clamav.json"
ALPINE_EOL_API = "https://endoflife.date/api/alpine-linux.json"
ALPINE_CDN = "https://dl-cdn.alpinelinux.org/alpine"
ALPINE_REPO = "community"
ALPINE_ARCH = "x86_64"

# How many days before an EOL date we start raising a ticket.
WARN_DAYS = 90

HTTP_TIMEOUT = 30


# ---------------------------------------------------------------------------
# Version helpers
# ---------------------------------------------------------------------------
def version_key(v: str | None) -> tuple[int, int, int, int]:
    """
    Turn a version string into a comparable tuple.

    Handles Alpine package versions ("1.4.4-r0"), upstream ClamAV releases
    ("1.5.3"), Alpine branches ("3.23" / "3.23.4") and deploy tags ("v0.5.5" -
    the leading "v" is ignored). The `-rN` package release is kept as a
    lowest-priority tiebreaker so "1.4.4-r1" > "1.4.4-r0".
    """
    if not v:
        return (0, 0, 0, 0)
    v = v.strip()
    rel = 0
    if "-r" in v:
        base, _, tail = v.partition("-r")
        rel = int(re.sub(r"\D", "", tail) or 0)
    else:
        base = v
    nums = tuple(int(p) for p in re.findall(r"\d+", base)[:3])
    nums += (0,) * (3 - len(nums))
    return (*nums, rel)


def series_of(clamav_version: str) -> str:
    """Return the ClamAV release series (major.minor), e.g. "1.4.4-r0" -> "1.4"."""
    nums = re.findall(r"\d+", clamav_version)
    return ".".join(nums[:2]) if len(nums) >= 2 else clamav_version


def days_until(eol) -> int | None:
    """
    Days from today until an endoflife.date `eol` field.

    Returns None when the field is a boolean (cycle has no scheduled EOL) or is
    unparseable. Negative means the date is already in the past.
    """
    if not isinstance(eol, str):
        return None
    try:
        eol_date = datetime.strptime(eol, "%Y-%m-%d").date()
    except ValueError:
        return None
    return (eol_date - date.today()).days


def normalize_tag(tag: str) -> str:
    """Ensure a deploy version has a single leading "v" (values already do)."""
    tag = tag.strip()
    return tag if tag.startswith("v") else f"v{tag}"


# ---------------------------------------------------------------------------
# 1. Deployed versions (clamav-deploy values, private GitLab)
# ---------------------------------------------------------------------------
def _gitlab_headers() -> dict:
    token = os.environ.get("GITLAB_TOKEN")
    if not token:
        raise SystemExit(
            "GITLAB_TOKEN is required to read clamav-deploy values from GitLab."
        )
    return {"PRIVATE-TOKEN": token}


def list_values_files() -> list[str]:
    """List the per-environment values files under clamav-deploy `values/`."""
    project = quote(CLAMAV_DEPLOY_PROJECT, safe="")
    resp = requests.get(
        f"{GITLAB_API}/projects/{project}/repository/tree",
        headers=_gitlab_headers(),
        params={"path": VALUES_PATH, "ref": DEPLOY_REF, "per_page": 100},
        timeout=HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    return [
        entry["path"]
        for entry in resp.json()
        if entry.get("type") == "blob" and entry["name"].endswith((".yaml", ".yml"))
    ]


def fetch_gitlab_file(path: str) -> str:
    """Fetch one file's raw content from clamav-deploy via the GitLab API."""
    project = quote(CLAMAV_DEPLOY_PROJECT, safe="")
    resp = requests.get(
        f"{GITLAB_API}/projects/{project}/repository/files/{quote(path, safe='')}/raw",
        headers=_gitlab_headers(),
        params={"ref": DEPLOY_REF},
        timeout=HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.text


def deployed_versions_from_values(values_files: dict[str, str]) -> dict:
    """
    Reduce raw {env_name: yaml_text} into deployed tag facts.

    Returns {per_env, tags, reference_tag, drift}. `reference_tag` is the lowest
    (most-behind) tag across all environments/components - the worst case for
    ClamAV currency / EOL. `drift` is True when the tags are not all identical.
    """
    per_env: dict[str, dict[str, str]] = {}
    all_tags: list[str] = []
    for env, text in values_files.items():
        data = yaml.safe_load(text) or {}
        comps = {}
        for key in VERSION_KEYS:
            section = data.get(key)
            if isinstance(section, dict) and section.get("version"):
                comps[key] = str(section["version"])
        if comps:
            per_env[env] = comps
            all_tags.extend(comps.values())

    if not all_tags:
        raise SystemExit(
            f"No {VERSION_KEYS} versions found in "
            f"{CLAMAV_DEPLOY_PROJECT}/{VALUES_PATH}"
        )

    return {
        "per_env": per_env,
        "tags": all_tags,
        "reference_tag": min(all_tags, key=version_key),
        "drift": len(set(all_tags)) > 1,
    }


def collect_deployed_versions() -> dict:
    """Fetch clamav-deploy values and reduce them to deployed tag facts."""
    values_files = {
        Path(path).stem: fetch_gitlab_file(path) for path in list_values_files()
    }
    return deployed_versions_from_values(values_files)


# ---------------------------------------------------------------------------
# 2. Shipped pins (clamav-http Dockerfiles, at the deployed tag)
# ---------------------------------------------------------------------------
def parse_dockerfile(text: str, label: str) -> dict:
    """
    Parse the ClamAV + Alpine versions pinned in a Dockerfile's text.

    Handles both `FROM alpine:3.23.4` and `FROM python:3.14-alpine3.23`, and
    `ENV CLAM_VERSION=1.4.4-r0` (or space-separated). `clamav` is None when the
    file does not pin CLAM_VERSION.
    """
    clam = re.search(r"CLAM_VERSION[=\s]+([0-9][^\s\\]*)", text)
    alpine = re.search(r"alpine:?(\d+\.\d+(?:\.\d+)?)", text)
    return {
        "path": label,
        "clamav": clam.group(1) if clam else None,
        "alpine": alpine.group(1) if alpine else None,
        "alpine_branch": ".".join(alpine.group(1).split(".")[:2]) if alpine else None,
    }


def fetch_dockerfile_at_tag(tag: str, path: str) -> str:
    """Fetch one clamav-http Dockerfile at a given tag (public GitHub raw)."""
    resp = requests.get(
        f"{CLAMAV_HTTP_RAW}/{normalize_tag(tag)}/{path}", timeout=HTTP_TIMEOUT
    )
    resp.raise_for_status()
    return resp.text


def collect_shipped_versions() -> dict:
    """
    Resolve the deployed tag to the ClamAV / Alpine pins it actually ships.

    Reads the deployed tag from clamav-deploy, then parses both clamav-http
    Dockerfiles at that tag. Returns the canonical shipped clamav / alpine_branch
    plus a `drift` flag covering both deploy drift (envs/components disagree) and
    Dockerfile drift (the two Dockerfiles disagree).
    """
    deployed = collect_deployed_versions()
    tag = deployed["reference_tag"]

    per_file = []
    for dockerfile in CLAMAV_DOCKERFILES:
        text = fetch_dockerfile_at_tag(tag, dockerfile)
        per_file.append(parse_dockerfile(text, f"{dockerfile}@{normalize_tag(tag)}"))

    clam_versions = {f["clamav"] for f in per_file if f["clamav"]}
    branch_versions = {f["alpine_branch"] for f in per_file if f["alpine_branch"]}

    return {
        "clamav": next(iter(clam_versions), None),
        "alpine_branch": next(iter(branch_versions), None),
        "per_file": per_file,
        "reference_tag": tag,
        "deployed": deployed,
        "drift": deployed["drift"]
        or len(clam_versions) > 1
        or len(branch_versions) > 1,
    }


# ---------------------------------------------------------------------------
# 3. Alpine-reachable versions (APKINDEX on the CDN)
# ---------------------------------------------------------------------------
def alpine_pkg_version(branch: str, pkg: str = "clamav") -> str | None:
    """
    Look up the version of `pkg` Alpine packages for a given branch.

    `branch` is an Alpine branch tag, e.g. "v3.23" or "edge". Downloads and
    parses the community APKINDEX; returns None if the branch/package is absent.
    """
    url = f"{ALPINE_CDN}/{branch}/{ALPINE_REPO}/{ALPINE_ARCH}/APKINDEX.tar.gz"
    resp = requests.get(url, timeout=HTTP_TIMEOUT)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()

    with tarfile.open(fileobj=io.BytesIO(resp.content), mode="r:gz") as tar:
        member = tar.extractfile("APKINDEX")
        index = member.read().decode() if member else ""

    for block in index.split("\n\n"):
        fields = dict(
            line.split(":", 1) for line in block.splitlines() if ":" in line
        )
        if fields.get("P") == pkg:
            return fields.get("V")
    return None


def reachable_clamav_versions(current_branch: str, alpine_data: list[dict]) -> dict:
    """
    Map each relevant Alpine branch to the clamav version it offers.

    Covers our current branch, every *newer* stable branch, and edge - the set
    the R1/R2/R3 rules reason over. Keys are "3.23"/"3.24"/"edge".
    """
    cur_key = version_key(current_branch)
    branches = {current_branch}
    for cycle in (c.get("cycle") for c in alpine_data):
        if cycle and version_key(cycle) > cur_key:
            branches.add(cycle)

    reachable = {}
    for branch in branches:
        reachable[branch] = alpine_pkg_version(f"v{branch}")
    reachable["edge"] = alpine_pkg_version("edge")
    return {b: v for b, v in reachable.items() if v}


# ---------------------------------------------------------------------------
# 4. Upstream release + EOL data (endoflife.date)
# ---------------------------------------------------------------------------
def retrieve_clamav_data() -> list[dict]:
    """Return endoflife.date's ClamAV cycles (latest release + eol per series)."""
    resp = requests.get(CLAMAV_EOL_API, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def retrieve_alpine_data() -> list[dict]:
    """Return endoflife.date's Alpine cycles (latest release + eol per branch)."""
    resp = requests.get(ALPINE_EOL_API, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def find_cycle(data: list[dict], cycle: str) -> dict | None:
    """Return the endoflife.date entry whose `cycle` matches, else None."""
    return next((c for c in data if str(c.get("cycle")) == cycle), None)


def upstream_latest(clamav_data: list[dict]) -> str | None:
    """The newest ClamAV release across all series (e.g. "1.5.3")."""
    latests = [c.get("latest") for c in clamav_data if c.get("latest")]
    return max(latests, key=version_key) if latests else None


# ---------------------------------------------------------------------------
# Decision logic  (R1, R2, R4, R5 -> tickets; R3 -> signal)
# ---------------------------------------------------------------------------
def clam_av_update_required(current: str, reachable_in_branch: str) -> bool:
    """R1 test: does our own Alpine branch already offer clamav > shipped?"""
    return version_key(reachable_in_branch) > version_key(current)


def alpine_update_required(current_branch_max: str, newer_branch_version: str) -> bool:
    """R2 test: does a newer stable branch offer clamav we can't get in-branch?"""
    return version_key(newer_branch_version) > version_key(current_branch_max)


def evaluate(shipped: dict, reachable: dict, clamav_data: list[dict],
             alpine_data: list[dict], warn_days: int = WARN_DAYS) -> list[dict]:
    """
    Apply the decision rules and return a list of findings.

    Each finding is a dict: {rule, actionable, priority, label, title, description}.
    `actionable=True` findings become Jira tickets; `actionable=False` (R3) are
    logged as a signal only.
    """
    findings: list[dict] = []
    shipped_clam = shipped["clamav"]
    branch = shipped["alpine_branch"]
    cur_max = reachable.get(branch)

    # R1 - in-branch bump (low risk: just repin CLAM_VERSION)
    if cur_max and clam_av_update_required(shipped_clam, cur_max):
        findings.append({
            "rule": "R1",
            "actionable": True,
            "priority": "Medium",
            "label": DEDUP_LABEL,
            "title": f"Bump ClamAV to {cur_max} in clamav Dockerfiles",
            "description": (
                f"Alpine {branch} now packages clamav {cur_max}, ahead of the "
                f"deployed {shipped_clam}.\n\nRepin CLAM_VERSION in: "
                + ", ".join(f["path"] for f in shipped["per_file"]) + "."
            ),
        })

    # R2 - base bump to reach a newer clamav a newer stable branch offers
    stable_newer = {
        b: v for b, v in reachable.items()
        if b != "edge" and version_key(b) > version_key(branch)
    }
    if stable_newer:
        best_branch = max(stable_newer, key=lambda b: version_key(stable_newer[b]))
        best_ver = stable_newer[best_branch]
        if cur_max and alpine_update_required(cur_max, best_ver):
            findings.append({
                "rule": "R2",
                "actionable": True,
                "priority": "Low",
                "label": DEDUP_LABEL,
                "title": f"Bump Alpine base {branch} -> {best_branch} to reach ClamAV {best_ver}",
                "description": (
                    f"Alpine {branch} is capped at clamav {cur_max}; branch "
                    f"{best_branch} offers {best_ver}. Reaching it needs an "
                    f"Alpine base bump ({branch} -> {best_branch}), a larger change "
                    f"than an in-branch repin."
                ),
            })

    # R4 - shipped ClamAV series approaching EOL
    clam_cycle = find_cycle(clamav_data, series_of(shipped_clam))
    if clam_cycle:
        d = days_until(clam_cycle.get("eol"))
        if d is not None and d <= warn_days:
            findings.append({
                "rule": "R4",
                "actionable": True,
                "priority": "High",
                "label": DEDUP_LABEL,
                "title": f"ClamAV {clam_cycle['cycle']} reaches EOL on {clam_cycle['eol']}",
                "description": (
                    f"Deployed ClamAV series {clam_cycle['cycle']} "
                    f"{'is already past EOL' if d < 0 else f'reaches EOL in {d} days'} "
                    f"({clam_cycle['eol']}). An EOL ClamAV eventually loses "
                    f"virus-definition updates - plan an upgrade."
                ),
            })

    # R5 - Alpine base branch approaching EOL
    alpine_cycle = find_cycle(alpine_data, branch)
    if alpine_cycle:
        d = days_until(alpine_cycle.get("eol"))
        if d is not None and d <= warn_days:
            findings.append({
                "rule": "R5",
                "actionable": True,
                "priority": "High",
                "label": DEDUP_LABEL,
                "title": f"Alpine {branch} base reaches EOL on {alpine_cycle['eol']}",
                "description": (
                    f"The Alpine {branch} base "
                    f"{'is already past EOL' if d < 0 else f'reaches EOL in {d} days'} "
                    f"({alpine_cycle['eol']}). Plan a base image bump."
                ),
            })

    # R3 - upstream ahead of Alpine: signal only, never a ticket
    up = upstream_latest(clamav_data)
    best_reachable = max(reachable.values(), key=version_key) if reachable else None
    if up and best_reachable and version_key(up) > version_key(best_reachable):
        findings.append({
            "rule": "R3",
            "actionable": False,
            "priority": None,
            "label": None,
            "title": f"ClamAV {up} released upstream; not yet in Alpine",
            "description": (
                f"Upstream ClamAV {up} is ahead of the best Alpine-reachable "
                f"{best_reachable}. Nothing to action until Alpine packages it - "
                f"R1/R2 will fire when it does."
            ),
        })

    return findings


# ---------------------------------------------------------------------------
# Jira
# ---------------------------------------------------------------------------
def build_title(finding: dict) -> str:
    return finding["title"]


def build_description(finding: dict) -> str:
    return finding["description"]


def build_fields(finding: dict) -> dict:
    return {
        "project": {"key": JIRA_PROJECT},
        "summary": build_title(finding),
        "description": build_description(finding),
        "issuetype": {"name": "Task"},
        "priority": {"name": finding["priority"]},
        "labels": [finding["label"]],
        JIRA_EPIC_FIELD: JIRA_EPIC_KEY,
    }


def open_ticket_titles(jira) -> set[str]:
    """Summaries of our own open, label-tagged tickets (for de-dup)."""
    jql = (
        f'project = {JIRA_PROJECT} AND labels = "{DEDUP_LABEL}" '
        f"AND statusCategory != Done"
    )
    issues = jira.jql(jql, fields="summary").get("issues", [])
    return {i["fields"]["summary"] for i in issues}


def ticket_already_exists(title: str, existing_titles: set[str]) -> bool:
    return title in existing_titles


def create_ticket(jira, finding: dict) -> str:
    result = jira.create_issue(fields=build_fields(finding))
    return result.get("key", str(result))


def print_finding(finding: dict) -> None:
    kind = "TICKET" if finding["actionable"] else "SIGNAL"
    print("=" * 70)
    print(f"[{finding['rule']}] {kind}"
          + (f" (priority {finding['priority']})" if finding["priority"] else ""))
    print(f"SUMMARY: {finding['title']}")
    print("--- DESCRIPTION ---")
    print(finding["description"])
    print("=" * 70)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def gather() -> tuple[dict, dict, list[dict], list[dict]]:
    """Collect everything the rules need: shipped, reachable, upstream, alpine."""
    shipped = collect_shipped_versions()
    if not shipped["clamav"] or not shipped["alpine_branch"]:
        raise SystemExit(
            f"Could not parse ClamAV/Alpine from tag {shipped['reference_tag']}: "
            f"{shipped['per_file']}"
        )
    clamav_data = retrieve_clamav_data()
    alpine_data = retrieve_alpine_data()
    reachable = reachable_clamav_versions(shipped["alpine_branch"], alpine_data)
    return shipped, reachable, clamav_data, alpine_data


def main() -> None:
    parser = argparse.ArgumentParser(description="ClamAV version checker (ACPENG-2944)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print findings without touching Jira")
    parser.add_argument("--warn-days", type=int, default=WARN_DAYS,
                        help=f"Days before EOL to raise a ticket (default {WARN_DAYS})")
    args = parser.parse_args()

    if not os.environ.get("GITLAB_TOKEN"):
        print("Error: GITLAB_TOKEN is not set (needed to read clamav-deploy values).")
        sys.exit(1)

    shipped, reachable, clamav_data, alpine_data = gather()

    deployed = shipped["deployed"]
    print("Deployed (from clamav-deploy values):")
    for env, comps in deployed["per_env"].items():
        print(f"  {env}: " + ", ".join(f"{k}={v}" for k, v in comps.items()))
    print(f"Reference tag (lowest): {shipped['reference_tag']}"
          + ("  [DRIFT across envs/components!]" if deployed["drift"] else ""))
    print(f"Shipped:   clamav {shipped['clamav']} on alpine {shipped['alpine_branch']}")
    print(f"Reachable: {reachable}")
    print(f"Upstream:  {upstream_latest(clamav_data)}\n")

    findings = evaluate(shipped, reachable, clamav_data, alpine_data, args.warn_days)
    tickets = [f for f in findings if f["actionable"]]
    signals = [f for f in findings if not f["actionable"]]

    for finding in signals:
        print_finding(finding)

    if not tickets:
        print("No actionable findings - nothing to file.")
        return

    if args.dry_run:
        for finding in tickets:
            print_finding(finding)
        print(f"\nDRY RUN - would file {len(tickets)} ticket(s).")
        return

    token = os.environ.get("JIRA_API_TOKEN")
    if not token:
        print("Error: JIRA_API_TOKEN environment variable is not set.")
        sys.exit(1)

    from atlassian import Jira
    jira = Jira(url=JIRA_URL, token=token)
    existing = open_ticket_titles(jira)

    for finding in tickets:
        if ticket_already_exists(finding["title"], existing):
            print(f"Skipped (already open): {finding['title']}")
            continue
        try:
            key = create_ticket(jira, finding)
        except Exception as exc:
            print(f"FAILED [{finding['rule']}]: {exc}")
            continue
        print(f"Created {key} [{finding['rule']}]: {finding['title']}")
        print(f"  {JIRA_URL}/browse/{key}")


if __name__ == "__main__":
    main()
