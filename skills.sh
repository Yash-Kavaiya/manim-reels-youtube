#!/usr/bin/env bash
#
# skills.sh — install the manim-reel skill + the reelgen engine locally.
#
# Run from inside a clone of this repo:
#     bash skills.sh
#
# On Windows, run it from Git Bash or WSL.
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="${REPO_DIR}/skills/manim-reel"
SKILL_DEST="${HOME}/.claude/skills/manim-reel"

echo "==> manim-reel installer"
echo "    repo: ${REPO_DIR}"

# --- 1. prerequisites -------------------------------------------------------
PY="$(command -v python3 || command -v python || true)"
if [ -z "${PY}" ]; then
  echo "error: Python 3.10+ is required and was not found on PATH" >&2
  exit 1
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "error: FFmpeg is required and must be on PATH" >&2
  exit 1
fi
echo "    python: ${PY}"
echo "    ffmpeg: $(command -v ffmpeg)"

# --- 2. install the reelgen engine -----------------------------------------
# Editable install so 'reelgen' / 'python -m reelgen' work from any directory.
echo "==> Installing the reelgen engine (pip install -e .)"
"${PY}" -m pip install -e "${REPO_DIR}"

# --- 3. install the skill for Claude Code ----------------------------------
echo "==> Installing the manim-reel skill into ${SKILL_DEST}"
mkdir -p "$(dirname "${SKILL_DEST}")"
rm -rf "${SKILL_DEST}"
cp -r "${SKILL_SRC}" "${SKILL_DEST}"

# --- 4. environment file ----------------------------------------------------
if [ ! -f "${REPO_DIR}/.env" ]; then
  cp "${REPO_DIR}/.env.example" "${REPO_DIR}/.env"
  echo "==> Created .env — add your DEEPGRAM_API_KEY to it"
fi

echo ""
echo "Done. The manim-reel skill is installed."
echo "  1. Add your Deepgram key to ${REPO_DIR}/.env"
echo "  2. In Claude Code, ask: \"make a reel about <topic>\""
echo "  3. Or use the CLI: reelgen build <storyboard.json> --out reel.mp4"
