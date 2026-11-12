#!/usr/bin/env bash
# One-line install of the self-improving agent harness into a project folder.
#
#   curl -fsSL https://raw.githubusercontent.com/rishikeshF/self-improving-agent-harness/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/rishikeshF/self-improving-agent-harness/main/install.sh | bash -s -- path/to/project
#   curl -fsSL https://raw.githubusercontent.com/rishikeshF/self-improving-agent-harness/main/install.sh | bash -s -- path/to/project --no-skeleton
#
# Keeps a copy of the harness in ~/.self-improving-agent-harness (updated on every run),
# then copies it into the project without overwriting any existing file.
set -euo pipefail

HARNESS_REPOSITORY_URL="https://github.com/rishikeshF/self-improving-agent-harness.git"
HARNESS_HOME="${HARNESS_HOME:-$HOME/.self-improving-agent-harness}"

# First argument is the project folder unless it is a flag; default is the current folder.
if [ "$#" -gt 0 ] && [ "${1#--}" = "$1" ]; then
  project_folder="$1"
  shift
else
  project_folder="."
fi

for required_command in git python3; do
  if ! command -v "$required_command" >/dev/null; then
    echo "error: $required_command is required" >&2
    exit 1
  fi
done

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "error: Python 3.11 or newer is required (found $(python3 --version))" >&2
  exit 1
fi

if [ -d "$HARNESS_HOME/.git" ]; then
  git -C "$HARNESS_HOME" pull -q --ff-only
else
  git clone -q --depth 1 "$HARNESS_REPOSITORY_URL" "$HARNESS_HOME"
fi

mkdir -p "$project_folder"
python3 "$HARNESS_HOME/scripts/install.py" "$project_folder" "$@"

if ! command -v uv >/dev/null; then
  echo
  echo "note: uv is not installed. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

echo
echo "Next:"
echo "  cd $project_folder && uv sync && make test"
echo "  claude    # then try /groom, /lanes, /goal, /retro (see HARNESS.md)"
