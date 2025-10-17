# POST /v1alpha/scan

## Example Requests

### Plain text response
```
curl -s -F "name=eicar" -F "file=@test/eicar.txt" http://clamav-http/v1alpha/scan
```

### JSON response
```
curl -s -H "Accept: application/json" -F "name=eicar" -F "file=@test/eicar.txt" http://clamav-http/v1alpha/scan
```

## Responses

### File is infected

Plain text:
```
HTTP/1.1 403 Forbidden
AV Response : FOUND
```

JSON:
```
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "status": "FOUND",
  "description": "Eicar-Test-Signature",
  "raw": "stream: Eicar-Test-Signature FOUND",
  "message": "FOUND"
}
```

### File is encrypted

Plain text:
```
HTTP/1.1 403 Forbidden
AV Response : FOUND
```

JSON:
```
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "status": "FOUND",
  "description": "Heuristics.Encrypted.Zip",
  "raw": "stream: Heuristics.Encrypted.Zip FOUND",
  "message": "FOUND"
}
```

### File is clean

Plain text:
```
HTTP/1.1 200 OK
AV Response : OK 
```

JSON:
```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "OK",
  "description": "",
  "raw": "stream: OK",
  "message": "OK"
}
```

### Error responses

Plain text:
```
HTTP/1.1 400 Bad Request
Invalid request: Error message here
```

JSON:
```
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "error": "Error message here" 
}
```
