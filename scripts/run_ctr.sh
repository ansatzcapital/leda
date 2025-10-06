#!/bin/bash
set -e

docker run --rm --platform linux/amd64 \
    -v .:/app/src -v /app/src/.pixi \
    --entrypoint bash -w /app/src \
    ghcr.io/prefix-dev/pixi:0.54.2-jammy \
    -c 'apt update && apt install -y git && \
    $@'
