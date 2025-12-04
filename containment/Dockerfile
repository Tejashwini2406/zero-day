FROM golang:1.21 AS builder
WORKDIR /workspace
COPY . .
RUN go mod tidy && CGO_ENABLED=0 GOOS=linux go build -a -ldflags="-w -s" -o operator operator.go

FROM alpine:3.18
RUN apk add --no-cache ca-certificates
WORKDIR /
COPY --from=builder /workspace/operator .
ENTRYPOINT ["/operator"]

