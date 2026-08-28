#!/bin/sh
set -eu

MODE=check
UV_VERSION=0.12.7
case "${1:-}" in
  ""|--check) ;;
  --install) MODE=install ;;
  *)
    echo "usage: $0 [--check|--install]" >&2
    exit 64
    ;;
esac

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
SELECTED=
SELECTED_REAL=
SELECTED_VERSION=

is_safe_candidate() {
  candidate=$1
  [ -x "$candidate" ] || return 1
  details=$(
    "$candidate" -c 'import os,sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"); print(os.path.realpath(sys.executable))' 2>/dev/null
  ) || return 1
  version=$(printf '%s\n' "$details" | sed -n '1p')
  real=$(printf '%s\n' "$details" | sed -n '2p')
  major=$(printf '%s' "$version" | cut -d. -f1)
  minor=$(printf '%s' "$version" | cut -d. -f2)
  [ "$major" -eq 3 ] 2>/dev/null || return 1
  [ "$minor" -ge 12 ] 2>/dev/null || return 1
  case "$real" in
    "$REPO_ROOT"/.venv/*|*/.venv/*|*/venv/*|/tmp/*|/private/tmp/*|/private/var/folders/*|*/work/*)
      return 1
      ;;
  esac
  SELECTED=$candidate
  SELECTED_REAL=$real
  SELECTED_VERSION=$version
  return 0
}

consider() {
  [ -n "$SELECTED" ] && return 0
  candidate=$1
  [ -n "$candidate" ] || return 0
  is_safe_candidate "$candidate" || true
}

if [ -n "${OBSERVATORY_PYTHON:-}" ]; then
  consider "$OBSERVATORY_PYTHON"
fi
if command -v brew >/dev/null 2>&1 && brew_prefix=$(brew --prefix python@3.12 2>/dev/null); then
  consider "$brew_prefix/bin/python3.12"
fi
if command -v uv >/dev/null 2>&1 && uv_python=$(uv python find '>=3.12,<4' 2>/dev/null); then
  consider "$uv_python"
fi
for command_name in python3.13 python3.12 python3; do
  if command -v "$command_name" >/dev/null 2>&1; then
    consider "$(command -v "$command_name")"
  fi
done

if [ -z "$SELECTED" ]; then
  cat >&2 <<'EOF'
No safe Python 3.12+ interpreter was found.

Use a maintained installation, then rerun this check:
- macOS Homebrew: https://formulae.brew.sh/formula/python@3.12
- Python.org: https://www.python.org/downloads/
- uv: https://docs.astral.sh/uv/guides/install-python/

Do not repoint a shared Python symlink or borrow an interpreter from another
project's .venv, temporary directory, or disposable work tree.
EOF
  exit 69
fi

printf '%s\n' \
  "status=ready" \
  "python_command=$SELECTED" \
  "python_real_path=$SELECTED_REAL" \
  "python_version=$SELECTED_VERSION" \
  "repository=$REPO_ROOT"

[ "$MODE" = install ] || exit 0

if [ -e "$REPO_ROOT/.venv" ]; then
  if [ ! -x "$REPO_ROOT/.venv/bin/python" ]; then
    echo "Existing .venv is incomplete; preserve or move it aside before retrying." >&2
    exit 73
  fi
  existing_real=$(
    "$REPO_ROOT/.venv/bin/python" -c 'import os,sys; print(os.path.realpath(sys._base_executable))' 2>/dev/null
  ) || {
    echo "Existing .venv cannot resolve its base interpreter; preserve or move it aside." >&2
    exit 73
  }
  if [ "$existing_real" != "$SELECTED_REAL" ]; then
    printf 'Existing .venv uses %s, selected safe base is %s.\n' "$existing_real" "$SELECTED_REAL" >&2
    echo "Preserve or move the existing environment aside; this script will not overwrite it." >&2
    exit 73
  fi
else
  "$SELECTED" -m venv "$REPO_ROOT/.venv"
fi

"$REPO_ROOT/.venv/bin/python" -m pip install --disable-pip-version-check "uv==$UV_VERSION"
UV_PROJECT_ENVIRONMENT="$REPO_ROOT/.venv" \
  "$REPO_ROOT/.venv/bin/python" -m uv sync --locked --extra dev \
  --python "$REPO_ROOT/.venv/bin/python"
"$REPO_ROOT/.venv/bin/observatory" --help >/dev/null
"$REPO_ROOT/.venv/bin/observatory" validate --root "$REPO_ROOT"
printf '%s\n' "install=complete" "cli=$REPO_ROOT/.venv/bin/observatory"
