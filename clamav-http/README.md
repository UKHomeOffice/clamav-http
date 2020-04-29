## clamav-http

Clamav proxy supporting the api of https://github.com/solita/clamav-rest/ and implemented in golang

### Usage

```
Usage of clamav-http:
  -host string
    	Address of the clamd instance (default "localhost")
  -listenPort int
    	TCP port that we should listen on (default 8080)
  -maxFileMem int
    	Maximum memory used to store uploaded files (excess is written to disk) (default 128)
  -port int
    	TCP port of the clamd instance (default 3310)
```

### API

| Version | Endpoint | Notes |
|---|---|---|
|[v0](/server/v0/doc.md) | / | Based on solita/clamav-rest |
|[v1alpha](/server/v1alpha/doc.md) | /v1alpha/ | Implements error code on malware found |