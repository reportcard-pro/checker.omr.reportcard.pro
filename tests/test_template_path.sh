#!/bin/bash
set -e
SCRIPT="$(dirname "$0")/../bin/omr_checker"
TMP_TPL="$(mktemp /tmp/test_template_XXXXX.json)"
echo '{}' > "$TMP_TPL"

output=$("$SCRIPT" --format jee --template-path "$TMP_TPL" --checksum test123 --python-path python3 2>&1 || true)
if echo "$output" | grep -q "mutually exclusive"; then
    echo "PASS: mutual exclusion detected"
else
    echo "FAIL: expected 'mutually exclusive' in output, got: $output"
    rm -f "$TMP_TPL"
    exit 1
fi

output=$("$SCRIPT" --template-path /nonexistent/path.json --checksum test456 --python-path python3 2>&1 || true)
if echo "$output" | grep -q "not found"; then
    echo "PASS: nonexistent template path detected"
else
    echo "FAIL: expected 'not found' in output, got: $output"
    rm -f "$TMP_TPL"
    exit 1
fi

rm -f "$TMP_TPL"
echo "All smoke tests passed"
