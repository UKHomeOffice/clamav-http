# POST /v1alpha/healthz

## Example Request

```
curl -s http://clamav-http/v1alpha/scan
```

## Response

### Clamav is working

```
HTTP/1.1 200 OK


healthcheck: OK
```

### Clamav is up but not working

```
HTTP/1.1 500 Internal Server Error


healthcheck: ERROR
```

### Clamav is not up or there was an error

```
HTTP/1.1 500 Internal Server Error


not okay
```