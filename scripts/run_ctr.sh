#!/bin/bash
# E.g.:
#   ./scripts/run_ctr.sh pixi run -e dev --frozen --locked just gen-integration-test3
set -ex

docker run --rm --platform linux/amd64 \
    -v .:/app/src -v /app/src/.pixi \
    --entrypoint bash -w /app/src \
    ghcr.io/prefix-dev/pixi:0.54.2-jammy \
    -c "apt update && apt install -y git && $*"
