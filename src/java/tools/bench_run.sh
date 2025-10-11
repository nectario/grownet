#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="build/java-classes"
mkdir -p "$OUT_DIR"

# Compile only core sources (exclude tests)
find src/java/ai/nektron/grownet -name '*.java' > .javac-sources.txt
javac -d "$OUT_DIR" @.javac-sources.txt

# Pass through args to Java
exec java -cp "$OUT_DIR" ai.nektron.grownet.bench.BenchJava "$@"
