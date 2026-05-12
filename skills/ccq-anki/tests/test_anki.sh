#!/usr/bin/env bash
# Regression tests for skills/anki/scripts/anki.sh
#
# Focus: ensure non-ASCII (UTF-8) payloads survive the trip through
#        argv -> curl -> AnkiConnect, especially on Windows (Git Bash /
#        MSYS2) where argv was historically re-encoded to the system
#        codepage (e.g. GBK), corrupting any non-ASCII bytes.
#
# Requirements:
#   - Anki desktop is running with AnkiConnect enabled on $ANKI_URL
#   - jq and curl are on PATH
#
# Usage:
#   bash skills/anki/tests/test_anki.sh
#
# Side effects:
#   Creates and then deletes a temporary deck named "_anki_regression_测试_<pid>".
#   No other Anki state is modified.

set -uo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ANKI="$SCRIPT_DIR/../scripts/anki.sh"
ANKI_URL="${ANKI_URL:-http://localhost:8765}"
export ANKI_URL

TEST_DECK="_anki_regression_测试_$$"
TEST_TAG="regression_测试_$$"

PASS=0
FAIL=0
FAILED_TESTS=()

pass() { PASS=$((PASS+1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL+1)); FAILED_TESTS+=("$1"); printf '  \033[31mFAIL\033[0m %s\n    %s\n' "$1" "${2:-}"; }

# Run an AnkiConnect call directly (independent of anki.sh) so cleanup
# does not depend on the code under test.
raw_invoke() {
  local body="$1"
  printf '%s' "$body" | curl -fsS "$ANKI_URL" --data-binary @-
}

cleanup() {
  echo
  echo "[cleanup] removing test deck: $TEST_DECK"
  local body
  body=$(jq -n --arg d "$TEST_DECK" \
    '{action:"deleteDecks",version:6,params:{decks:[$d],cardsToo:true}}')
  raw_invoke "$body" >/dev/null 2>&1 || true
}
trap cleanup EXIT

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 2; }
}
require curl
require jq

# Preflight: AnkiConnect reachable
if ! raw_invoke '{"action":"version","version":6}' | grep -q '"result": 6'; then
  echo "AnkiConnect not reachable at $ANKI_URL" >&2
  exit 2
fi

echo "=== anki.sh regression tests ==="
echo "ANKI_URL : $ANKI_URL"
echo "anki.sh  : $ANKI"
echo "deck     : $TEST_DECK"
echo

# --- 1) Basic ASCII operations -------------------------------------------
echo "[1] basic ASCII operations"

out=$("$ANKI" models 2>&1)
if echo "$out" | jq -e 'type=="array"' >/dev/null 2>&1; then
  pass "models returns JSON array"
else
  fail "models returns JSON array" "$out"
fi

out=$("$ANKI" decks 2>&1)
if echo "$out" | jq -e 'type=="object"' >/dev/null 2>&1; then
  pass "decks returns JSON object"
else
  fail "decks returns JSON object" "$out"
fi

# --- 2) Setup test deck ---------------------------------------------------
echo
echo "[2] setup test deck (UTF-8 deck name)"

body=$(jq -n --arg d "$TEST_DECK" \
  '{action:"createDeck",version:6,params:{deck:$d}}')
resp=$(raw_invoke "$body")
if echo "$resp" | grep -q '"error": null'; then
  pass "create deck '$TEST_DECK'"
else
  fail "create deck '$TEST_DECK'" "$resp"
  exit 1
fi

# --- 3) Regression: UTF-8 in argv (decks --stats path) -------------------
echo
echo "[3] UTF-8 in invoke argv (the original Windows/GBK bug)"

# decks --stats internally builds a findCards query that embeds the deck
# name (UTF-8) into the JSON body and sends it to AnkiConnect. On Windows
# this previously failed with: 'utf-8' codec can't decode byte 0xc8 ...
out=$("$ANKI" decks --stats 2>&1)
if echo "$out" | jq -e --arg d "$TEST_DECK" 'map(.name)|index($d)!=null' >/dev/null 2>&1; then
  pass "decks --stats includes UTF-8 deck name"
else
  fail "decks --stats includes UTF-8 deck name" "$out"
fi

# Direct find with a UTF-8 deck-scoped query
out=$("$ANKI" find "deck:\"$TEST_DECK\"" 2>&1)
if echo "$out" | jq -e 'type=="array"' >/dev/null 2>&1; then
  pass "find with UTF-8 deck name in query"
else
  fail "find with UTF-8 deck name in query" "$out"
fi

# --- 4) Add note with UTF-8 fields, tags, then find/info/update/delete ---
echo
echo "[4] add/find/info/update/delete with UTF-8 fields and tags"

# Pick any available model with >= 2 fields. We don't care which one;
# we only want to verify UTF-8 round-trips through add / info / update.
MODEL=""
F1=""; F2=""
models_json=$("$ANKI" models 2>/dev/null)
# Strip CR: jq on Git Bash / MSYS2 emits CRLF line endings, which would
# otherwise leak into the model name and break exact-match lookups.
# Skip image-occlusion-style models since they need image data, not text.
while IFS= read -r m; do
  m="${m%$'\r'}"
  [[ -z "$m" ]] && continue
  # Skip image-occlusion and cloze models: they need image data or
  # {{c1::...}} markers respectively, which would fail for plain text.
  case "$m" in
    *图片*|*Image*|*image*|*Occlusion*|*occlusion*|*遮盖*) continue ;;
    *填空*|*Cloze*|*cloze*) continue ;;
  esac
  fields_json=$("$ANKI" fields "$m" 2>/dev/null)
  n=$(echo "$fields_json" | jq 'length' 2>/dev/null || echo 0)
  if [[ "$n" -ge 2 ]]; then
    MODEL="$m"
    F1=$(echo "$fields_json" | jq -r '.[0]' | tr -d '\r')
    F2=$(echo "$fields_json" | jq -r '.[1]' | tr -d '\r')
    break
  fi
done < <(echo "$models_json" | jq -r '.[]')

if [[ -z "$MODEL" ]]; then
  fail "discover a usable model" "no model with >=2 fields found"
else
  pass "discover usable model: '$MODEL' (fields: '$F1','$F2')"
fi

note_id=""
if [[ -n "$MODEL" ]]; then
  V1="中文问题：什么是 ==SRS==？日本語・Ελληνικά"
  V2="**间隔重复系统** — Spaced Repetition System."
  fields=$(jq -n --arg f1 "$F1" --arg v1 "$V1" --arg f2 "$F2" --arg v2 "$V2" \
    '{($f1):$v1,($f2):$v2}')
  add_out=$("$ANKI" add "$TEST_DECK" "$MODEL" "$fields" --tags "$TEST_TAG" 2>&1)
  note_id=$(echo "$add_out" | tr -d '[:space:]')
  if [[ "$note_id" =~ ^[0-9]+$ ]]; then
    pass "add note with UTF-8 fields and UTF-8 tag (id=$note_id)"
  else
    fail "add note with UTF-8 fields and UTF-8 tag" "$add_out"
    note_id=""
  fi
fi

if [[ -n "$note_id" ]]; then
  out=$("$ANKI" find "tag:$TEST_TAG" 2>&1)
  if echo "$out" | jq -e --argjson id "$note_id" 'index($id)!=null' >/dev/null 2>&1; then
    pass "find by UTF-8 tag returns the new note"
  else
    fail "find by UTF-8 tag returns the new note" "$out"
  fi

  out=$("$ANKI" info "$note_id" 2>&1)
  if echo "$out" | jq -e --arg f "$F1" '.[0].fields[$f].value | contains("中文问题")' >/dev/null 2>&1; then
    pass "info preserves UTF-8 in field values"
  else
    fail "info preserves UTF-8 in field values" "$out"
  fi

  upd=$(jq -n --arg f2 "$F2" '{($f2):"**已更新**：间隔重复系统 (SRS)。"}')
  out=$("$ANKI" update "$note_id" "$upd" 2>&1)
  out2=$("$ANKI" info "$note_id" 2>&1)
  if echo "$out2" | jq -e --arg f "$F2" '.[0].fields[$f].value | contains("已更新")' >/dev/null 2>&1; then
    pass "update applies UTF-8 field value"
  else
    fail "update applies UTF-8 field value" "$out2 / first call: $out"
  fi
fi

# --- 5) add-bulk with UTF-8 ----------------------------------------------
echo
echo "[5] add-bulk with UTF-8 fields"

if [[ -n "$MODEL" ]]; then
  bulk=$(jq -n --arg f1 "$F1" --arg f2 "$F2" \
    '[{($f1):"日本語：質問1",($f2):"答え1"},
      {($f1):"Ελληνικά: ερώτηση",($f2):"απάντηση"}]')
  out=$("$ANKI" add-bulk "$TEST_DECK" "$MODEL" "$bulk" --tags "$TEST_TAG" 2>&1)
  count=$(echo "$out" | jq 'map(select(. != null)) | length' 2>/dev/null || echo 0)
  if [[ "$count" == "2" ]]; then
    pass "add-bulk returns 2 ids for UTF-8 notes"
  else
    fail "add-bulk returns 2 ids for UTF-8 notes" "$out"
  fi
fi

# --- summary --------------------------------------------------------------
echo
echo "=== summary ==="
echo "passed: $PASS"
echo "failed: $FAIL"
if [[ $FAIL -gt 0 ]]; then
  printf 'failed tests:\n'
  printf '  - %s\n' "${FAILED_TESTS[@]}"
  exit 1
fi
exit 0
