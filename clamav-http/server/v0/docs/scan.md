# POST /scan 

## Example Request

```
curl -s -F "name=eicar" -F "file=@test/eicar.txt" "$1/v1alpha/scan"
```

## Response

### File is infected

```
HTTP/1.1 200 OK


Everything ok : false
```

### File is clean

```
HTTP/1.1 200 OK


Everything ok : true
```