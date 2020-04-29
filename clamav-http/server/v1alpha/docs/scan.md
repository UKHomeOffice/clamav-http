# POST /v1alpha/scan 

## Example Request

```
curl -s -F "name=eicar" -F "file=@test/eicar.txt" http://clamav-http/v1alpha/scan
```

## Response

### File is infectes

```
HTTP/1.1 403 Forbidden


Everything ok : false
```

### File is clean

```
HTTP/1.1 200 OK


Everything ok : true
```