FROM golang:1.26.4-alpine3.23 AS builder

WORKDIR /go/src/github.com/ukhomeoffice/clamav-http/clamav-http

COPY go.mod go.sum main.go ./

COPY server/  ./server/

RUN CGO_ENABLED=0 GOOS=linux go install -v \
            github.com/ukhomeoffice/clamav-http/clamav-http

FROM alpine:3.23

RUN apk update && apk upgrade --no-cache && \
    apk --no-cache add ca-certificates

RUN addgroup -g 1000 -S app && \
    adduser -u 1000 -S app -G app

USER 1000

COPY --from=builder /go/bin/clamav-http /clamav-http

EXPOSE 8080

ENTRYPOINT ["/clamav-http"]
