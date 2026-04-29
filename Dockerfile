# syntax=docker/dockerfile:1.7
FROM golang:1.25.7-bookworm AS builder

WORKDIR /src

COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

COPY internal ./internal
COPY cmd ./cmd

RUN --mount=type=cache,target=/root/.cache/go-build \
    --mount=type=cache,target=/go/pkg/mod \
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -trimpath -ldflags="-s -w" \
    -o /out/build-class-change-notifications \
    ./cmd/build-class-change-notifications

RUN --mount=type=cache,target=/root/.cache/go-build \
    --mount=type=cache,target=/go/pkg/mod \
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -trimpath -ldflags="-s -w" \
    -o /out/dispatch-notifications \
    ./cmd/dispatch-notifications

FROM gcr.io/distroless/static-debian12:nonroot

COPY --from=builder /out/build-class-change-notifications /bin/build-class-change-notifications
COPY --from=builder /out/dispatch-notifications /bin/dispatch-notifications

USER nonroot:nonroot
