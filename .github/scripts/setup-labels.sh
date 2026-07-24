#!/usr/bin/env bash
# Creates (or updates) the standard label set for this repository.
#
# Requires: GitHub CLI (`gh`) authenticated with write access to the repo.
# Usage:
#   ./.github/scripts/setup-labels.sh [owner/repo]
#
# If no repo is given, it defaults to the current directory's repo (via `gh`'s
# auto-detection from the git remote).

set -euo pipefail

REPO_ARG=()
if [[ $# -ge 1 ]]; then
  REPO_ARG=(--repo "$1")
fi

create_label() {
  local name="$1" color="$2" description="$3"
  if gh label create "$name" --color "$color" --description "$description" --force "${REPO_ARG[@]}"; then
    echo "✔ $name"
  else
    echo "✘ failed: $name" >&2
  fi
}

create_label "bug"              "d73a4a" "Something isn't working as expected"
create_label "enhancement"      "a2eeef" "New feature or request"
create_label "question"         "d876e3" "Further information is requested"
create_label "documentation"    "0075ca" "Improvements or additions to documentation"
create_label "triage"           "fbca04" "Needs initial review/categorization by a maintainer"
create_label "needs-info"       "f9d0c4" "Waiting on more details from the reporter"
create_label "confirmed"        "0e8a16" "Reproduced and verified - ready to be worked on"
create_label "wontfix"          "ffffff" "This will not be worked on"
create_label "duplicate"        "cfd3d7" "This issue or PR already exists"
create_label "invalid"          "e4e669" "This doesn't seem right / not a valid issue"
create_label "good first issue" "7057ff" "Good for newcomers to the codebase"
create_label "help wanted"      "008672" "Extra attention or community contribution welcome"

echo "Done."
