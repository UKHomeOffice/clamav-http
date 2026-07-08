#!/usr/bin/env python3
"""
Create Jira tickets for ACP ECR images with critical or high CVEs.

Usage:
    python3 scripts/create_vuln_tickets.py             # creates 1 ticket
    python3 scripts/create_vuln_tickets.py --dry-run   # prints payload, no API call
    python3 scripts/create_vuln_tickets.py --all       # creates all tickets
    python3 scripts/create_vuln_tickets.py --image acp/dind  # specific base image
    python3 scripts/create_vuln_tickets.py --auto      # CI mode: process all eligible
                                                       # images, persist de-dup state
    python3 scripts/create_vuln_tickets.py --auto --state-file s3://bucket/jira/created_tickets.json

Requires:
    export JIRA_TOKEN="your-PAT"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

from atlassian import Jira

JIRA_URL = "https://collaboration.homeoffice.gov.uk/jira"
JIRA_PROJECT = "ACPENG"
JIRA_EPIC_FIELD = "customfield_10006"
JIRA_EPIC_KEY = "ACPENG-2598"


WORKSPACE = Path(__file__).parent.parent / "workspace"


def get_current_versions(dockerfile_path):
    """
    Reads the Dockerfile to get the current versions
    of Alpine and ClamAV
    """
    pass


def retrieve_latest_clam_av_versions() -> list[str]:
    """
    Calls https://api.github.com/repos/Cisco-Talos/clamav/releases?per_page=5
    to get the latest 5 ClamAV releases 
    """
    pass


def retrieve_latest_alpine_version():
    """
    Retrieves the latest alpine version with a ClamAV
    community package
    """


def get_latest_lts_version() -> float:
    """
    Filters ClamAV versions to return the most-recent
    LTS version (1.4.X)
    """
    pass


def clam_av_update_required(current_clam_av_ver, latest_clam_av_ver) -> bool:
    """
    Compares the latest ClamAV LTS version against
    the current version"""
    pass


def alpine_update_required(current_alpine_ver, latest_alpine_ver) -> bool:
    """
    Compares the latest Alpine version against
    the current version"""
    pass


def build_title(latest_clam_av_ver) -> str:
    """
    Builds the Jira ticket title from version"""
    pass


def ticket_already_exists(ticket_title: str) -> bool:
    """
    Checks if a ticket already exist for this upgrade
    """
    pass


def build_description(current_clam_av_ver, latest_clam_av_ver) -> str:
    """
    Builds the Jira ticket description indicating the upgrade required
    """


def build_fields(image: dict) -> dict:
    return {
        "project": {"key": JIRA_PROJECT},
        "summary": build_title(image),
        "description": build_description(image),
        "issuetype": {"name": "Task"},
        "priority": {"name": image["priority"]},
        JIRA_EPIC_FIELD: JIRA_EPIC_KEY,
    }


def print_dry_run(image: dict) -> None:
    fields = build_fields(image)
    print("=" * 70)
    print(f"SUMMARY:     {fields['summary']}")
    print(f"PROJECT:     {JIRA_PROJECT}")
    print(f"TYPE:        Task")
    print(f"PRIORITY:    {image['priority']}")
    print(f"EPIC:        {JIRA_EPIC_KEY}")
    print(f"TAGS:        {len(image['affected_tags'])} affected")
    print(f"REPOS:       {len(image['all_repos'])} repos")
    latest = image.get("latest_tag")
    if latest:
        print(f"LATEST TAG:  :{latest['tag']} — {latest['critical']} critical, {latest['high']} high")
    print()
    print("--- DESCRIPTION ---")
    print(fields["description"])
    print("=" * 70)


def create_ticket(jira: Jira, image: dict) -> str:
    fields = build_fields(image)
    result = jira.create_issue(fields=fields)
    return result.get("key", str(result))





def main() -> None:
    parser = argparse.ArgumentParser(description="Create Jira tickets for vulnerable ACP images")
    parser.add_argument("--dry-run", action="store_true", help="Print ticket fields without creating")
    parser.add_argument("--all", action="store_true", help="Create tickets for all vulnerable base images")
    parser.add_argument("--image", default=None, help="Target a specific base image (e.g. acp/dind)")
    parser.add_argument("--auto", action="store_true",
                        help="CI mode: process every eligible image and persist de-dup state")
    parser.add_argument("--state-file", default=None,
                        help="Path or s3:// URL holding the {short_base: jira_key} de-dup map")
    args = parser.parse_args()

    images, skipped = load_and_group(args.image)

    if not images and not skipped:
        print("No vulnerable images found matching criteria.")
        sys.exit(0)

    if not images:
        print("No images to process — all were skipped (see below).\n")

    state: dict = {}
    state_label = None
    if args.state_file:
        state, state_label = _load_state(args.state_file)
        before = len(images)
        images = [img for img in images if img["short_base"] not in state]
        print(f"De-dup: {before - len(images)} image(s) already filed (state: {state_label}).")

    if args.auto:
        pass  # process everything that survived the de-dup filter
    elif not args.all and not args.image:
        images = images[:1]

    print(f"{'DRY RUN — ' if args.dry_run else ''}Processing {len(images)} base image(s)...\n")

    if args.dry_run:
        for image in images:
            print_dry_run(image)
    elif images:
        token = os.environ.get("JIRA_TOKEN")
        if not token:
            print("Error: JIRA_TOKEN environment variable is not set.")
            sys.exit(1)

        jira = Jira(url=JIRA_URL, token=token)

        for image in images:
            try:
                key = create_ticket(jira, image)
            except Exception as e:
                print(f"FAILED: {image['short_base']} — {e}")
                continue
            state[image["short_base"]] = key
            print(f"Created: {key} — {image['short_base']} ({image['priority']})")
            print(f"  {JIRA_URL}/browse/{key}")

        if args.state_file:
            _save_state(args.state_file, state)
            print(f"\nState saved: {state_label} ({len(state)} entries)")

    if skipped:
        print(f"\n--- {len(skipped)} image(s) skipped (latest tag not found in latest_tags.json) ---")
        for name in skipped:
            print(f"  {name}")


if __name__ == "__main__":
    main()
