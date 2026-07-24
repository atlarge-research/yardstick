#!/usr/bin/env bash
#
# Uninstall Yardstick/Joystick from the host it is run on.
#
# This is what the GUI's Uninstall tab runs: the server pipes this file to the
# connected host (local or SSH) with the YS_* variables below preset. It also
# works standalone with the equivalent command-line flags.
#
# Reverses what the Joystick environment setup pipeline (gui/server/environment.js)
# and the experiment scripts (gui/server/scripts.js) install:
#
#   - the 'yardstick' conda env and the Miniconda that hosts it
#     ($HOME/miniconda3, or /var/scratch/$USER/miniconda3 on DAS)
#   - the conda init block in ~/.bashrc
#   - per-run working directories (~/yardstick/run, /var/scratch/$USER/yardstick)
#   - local-mode Docker containers (ys-local-*) and the yardstick-node image
#   - leftover PaperMC / Telegraf / bot processes owned by this user
#
# Experiment results in ~/experiments are KEPT unless --purge is given.
# System packages installed via apt/dnf/brew (java, rsync, wget, git, node) are
# never removed: they are shared with the rest of the machine.
#
# Usage: uninstall.sh [options]
#
set -euo pipefail

# Env defaults let the GUI drive the script without argv; flags still win.
DRY_RUN="${YS_DRY_RUN:-0}"
ASSUME_YES="${YS_YES:-0}"
PURGE="${YS_PURGE:-0}"
REMOVE_NVM="${YS_NVM:-0}"
KEEP_PROCESSES="${YS_KEEP_PROCESSES:-0}"

usage() {
  cat <<'EOF'
Usage: uninstall.sh [options]

Options:
  -n, --dry-run   Show what would be removed, change nothing.
  -y, --yes       Do not ask for confirmation.
      --purge     Also remove experiment results (~/experiments), the AWS key
                  ~/.ssh/yardstick_exp.pem, the /swapfile created by setup, and
                  the Joystick desktop-app config directories.
      --nvm       Also remove ~/.nvm (installed on worker nodes for the bot
                  workload; skipped by default since it may predate Yardstick).
      --keep-processes
                  Do not kill leftover PaperMC/Telegraf/bot processes.
  -h, --help      Show this help.

Equivalent environment variables (used by the GUI): YS_DRY_RUN, YS_YES,
YS_PURGE, YS_NVM, YS_KEEP_PROCESSES, and YS_SCRATCH_USER to override the
/var/scratch/<user> directory scanned on DAS.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    -n|--dry-run) DRY_RUN=1 ;;
    -y|--yes) ASSUME_YES=1 ;;
    --purge) PURGE=1 ;;
    --nvm) REMOVE_NVM=1 ;;
    --keep-processes) KEEP_PROCESSES=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

USER_NAME="${USER:-$(id -un)}"
SCRATCH="/var/scratch/${YS_SCRATCH_USER:-$USER_NAME}"

# --- collect targets -------------------------------------------------------
# Only paths that actually exist end up in TARGETS, so the plan we print is the
# plan we execute.
TARGETS=()
NOTES=()

add_target() {
  local path="$1"
  case "$path" in
    ''|'/'|"$HOME") return 0 ;;   # never
  esac
  [ -e "$path" ] || return 0
  TARGETS+=("$path")
  return 0
}

# Setup installs Miniconda only when it is missing, so a Miniconda that also
# holds other envs predates Yardstick: drop just the 'yardstick' env there.
for base in "$HOME" "$SCRATCH"; do
  [ -d "$base" ] || continue
  conda_dir="$base/miniconda3"
  if [ -d "$conda_dir" ]; then
    # ls (not -A): conda's own dotfile probes (.conda_envs_dir_test) are not envs.
    other_envs=$(ls "$conda_dir/envs" 2>/dev/null | grep -v '^yardstick$' || true)
    if [ -n "$other_envs" ]; then
      add_target "$conda_dir/envs/yardstick"
      NOTES+=("kept $conda_dir: it holds other conda envs ($(echo "$other_envs" | tr '\n' ' ')), only the 'yardstick' env is removed")
    else
      add_target "$conda_dir"
    fi
  fi
  add_target "$base/yardstick/run"
done

# DAS keeps the whole tree under scratch; drop it if the run dir was all it held.
if [ -d "$SCRATCH/yardstick" ] && [ -z "$(ls -A "$SCRATCH/yardstick" 2>/dev/null | grep -v '^run$' || true)" ]; then
  add_target "$SCRATCH/yardstick"
fi

if [ "$REMOVE_NVM" = 1 ]; then
  add_target "$HOME/.nvm"
else
  [ -d "$HOME/.nvm" ] && NOTES+=("kept ~/.nvm (enable 'Remove ~/.nvm' to delete it)") || true
fi

if [ "$PURGE" = 1 ]; then
  add_target "$HOME/experiments"
  add_target "$HOME/.ssh/yardstick_exp.pem"
  for cfg in "$HOME/.config/Joystick" "$HOME/.config/yardstick-gui" "$HOME/.config/Yardstick"; do
    add_target "$cfg"
  done
else
  [ -d "$HOME/experiments" ] && NOTES+=("kept experiment results in ~/experiments (enable 'Also delete experiment results' to remove them)") || true
  [ -f "$HOME/.ssh/yardstick_exp.pem" ] && NOTES+=("kept ~/.ssh/yardstick_exp.pem (needed to SSH into any EC2 nodes still running)") || true
fi

# --- docker artifacts ------------------------------------------------------
DOCKER_CONTAINERS=""
DOCKER_IMAGES=""
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  DOCKER_CONTAINERS=$(docker ps -a --filter 'name=^ys-local-' --format '{{.Names}}' 2>/dev/null || true)
  DOCKER_IMAGES=$(docker images --filter 'reference=yardstick-node' --format '{{.Repository}}:{{.Tag}}' 2>/dev/null || true)
fi

# --- leftover processes ----------------------------------------------------
# These target the PaperMC server jar, the bot launcher, and the monitoring agent
# started with its per-host config.
#
# Two rules when touching this list, both learned the hard way:
#   1. Keep the [x] bracket form. pgrep -f matches full command lines, and when
#      the GUI pipes this file to a shell, the script text IS a command line.
#      Written plainly, a pattern matches the shell running the script, which
#      then kills itself before removing anything.
#   2. Never spell a matching command line out in a comment either, for exactly
#      the same reason. Describe it instead. is_own_process below is the backstop.
PROC_PATTERNS=(
  'paper-1[.]20[.]1-.*[.]jar'
  'node workload_bot[.]js'
  'telegraf --config telegraf[-]'
)
# True if pid is this shell, an ancestor of it, or one of its own children
# (command substitutions briefly inherit this shell's command line).
is_own_process() {
  local pid="$1" hops=0 cur
  [ "$pid" = "$$" ] && return 0
  [ "$pid" = "$PPID" ] && return 0
  cur="$pid"
  while [ "$hops" -lt 12 ]; do
    cur=$(ps -o ppid= -p "$cur" 2>/dev/null | tr -d ' ')
    [ -z "$cur" ] && return 1
    [ "$cur" = "1" ] && return 1
    [ "$cur" = "$$" ] && return 0
    hops=$((hops + 1))
  done
  return 1
}

PROC_PIDS=""
if [ "$KEEP_PROCESSES" = 0 ]; then
  for pat in "${PROC_PATTERNS[@]}"; do
    pids=$(pgrep -u "$USER_NAME" -f "$pat" 2>/dev/null || true)
    [ -n "$pids" ] && PROC_PIDS="$PROC_PIDS $pids" || true
  done
  _kept=""
  for p in $PROC_PIDS; do
    is_own_process "$p" && continue
    # Skip anything that already exited between the scan and now.
    kill -0 "$p" 2>/dev/null || continue
    _kept="$_kept $p"
  done
  PROC_PIDS=$(echo "$_kept" | tr ' ' '\n' | sed '/^$/d' | sort -u | tr '\n' ' ')
fi

# --- ~/.bashrc conda block -------------------------------------------------
# Only meaningful if the Miniconda the block points at is going away.
BASHRC="$HOME/.bashrc"
STRIP_CONDA_BLOCK=0
if [ -f "$BASHRC" ] && grep -q '# >>> conda initialize >>>' "$BASHRC"; then
  for t in ${TARGETS[@]+"${TARGETS[@]}"}; do
    case "$t" in */miniconda3) STRIP_CONDA_BLOCK=1 ;; esac
  done
fi

# --- swapfile --------------------------------------------------------------
REMOVE_SWAPFILE=0
if [ "$PURGE" = 1 ] && [ -e /swapfile ]; then
  REMOVE_SWAPFILE=1
fi

# --- plan ------------------------------------------------------------------
echo "Yardstick/Joystick uninstall on ${HOSTNAME:-$(uname -n)} as ${USER_NAME}"
echo

nothing=1
if [ ${#TARGETS[@]} -gt 0 ]; then
  nothing=0
  echo "Directories and files to remove:"
  for t in "${TARGETS[@]}"; do
    size=$(du -sh "$t" 2>/dev/null | cut -f1 || echo '?')
    printf '  %-56s %s\n' "$t" "$size"
  done
  echo
fi

if [ -n "$DOCKER_CONTAINERS" ] || [ -n "$DOCKER_IMAGES" ]; then
  nothing=0
  echo "Docker artifacts to remove:"
  for c in $DOCKER_CONTAINERS; do echo "  container $c"; done
  for i in $DOCKER_IMAGES; do echo "  image     $i"; done
  echo
fi

if [ -n "$PROC_PIDS" ]; then
  nothing=0
  echo "Leftover processes to stop:"
  for p in $PROC_PIDS; do
    printf '  pid %-8s %s\n' "$p" "$(ps -p "$p" -o args= 2>/dev/null | cut -c1-90)"
  done
  echo
fi

if [ "$STRIP_CONDA_BLOCK" = 1 ]; then
  nothing=0
  echo "Shell config:"
  echo "  remove the 'conda initialize' block from ~/.bashrc (backup: ~/.bashrc.yardstick-uninstall.bak)"
  echo
fi

if [ "$REMOVE_SWAPFILE" = 1 ]; then
  nothing=0
  echo "Swap:"
  echo "  swapoff and remove /swapfile (needs passwordless sudo; skipped if unavailable)"
  echo
fi

if [ "$nothing" = 1 ]; then
  echo "Nothing to do: no Yardstick installation found for this user."
  for n in "${NOTES[@]:-}"; do [ -n "$n" ] && echo "Note: $n" || true; done
  exit 0
fi

for n in "${NOTES[@]:-}"; do [ -n "$n" ] && echo "Note: $n" || true; done
echo "Note: system packages (java, node, rsync, wget, git) are left installed."
echo

if [ "$DRY_RUN" = 1 ]; then
  echo "Dry run: nothing was changed."
  exit 0
fi

if [ "$ASSUME_YES" = 0 ]; then
  printf 'Proceed? [y/N] '
  read -r reply
  case "$reply" in
    y|Y|yes|YES) ;;
    *) echo "Aborted."; exit 1 ;;
  esac
  echo
fi

# --- execute ---------------------------------------------------------------
if [ -n "$PROC_PIDS" ]; then
  for p in $PROC_PIDS; do
    kill "$p" 2>/dev/null || true
  done
  sleep 2
  for p in $PROC_PIDS; do
    kill -0 "$p" 2>/dev/null && kill -9 "$p" 2>/dev/null || true
  done
  echo "[OK] Stopped leftover processes."
fi

for c in $DOCKER_CONTAINERS; do
  docker rm -f "$c" >/dev/null 2>&1 && echo "[OK] Removed container $c" || echo "[warn] Could not remove container $c" >&2
done
for i in $DOCKER_IMAGES; do
  docker rmi -f "$i" >/dev/null 2>&1 && echo "[OK] Removed image $i" || echo "[warn] Could not remove image $i" >&2
done

for t in ${TARGETS[@]+"${TARGETS[@]}"}; do
  if rm -rf "$t"; then
    echo "[OK] Removed $t"
  else
    echo "[warn] Could not remove $t" >&2
  fi
done

if [ "$STRIP_CONDA_BLOCK" = 1 ]; then
  cp "$BASHRC" "$BASHRC.yardstick-uninstall.bak"
  awk '
    /# >>> conda initialize >>>/ { skip = 1 }
    !skip { print }
    /# <<< conda initialize <<</ { skip = 0 }
  ' "$BASHRC.yardstick-uninstall.bak" > "$BASHRC"
  echo "[OK] Removed conda init block from ~/.bashrc (backup at $BASHRC.yardstick-uninstall.bak)"
fi

if [ "$REMOVE_SWAPFILE" = 1 ]; then
  if sudo -n true 2>/dev/null; then
    sudo -n swapoff /swapfile 2>/dev/null || true
    sudo -n rm -f /swapfile && echo "[OK] Removed /swapfile"
  else
    echo "[warn] No passwordless sudo; /swapfile left in place. Remove with: sudo swapoff /swapfile && sudo rm /swapfile" >&2
  fi
fi

# --- verify ----------------------------------------------------------------
# Removal can fail quietly (permissions, NFS handles, a process holding a file),
# so re-check instead of trusting the loops above.
LEFTOVER=""
for t in ${TARGETS[@]+"${TARGETS[@]}"}; do
  [ -e "$t" ] && LEFTOVER="$LEFTOVER $t" || true
done

if [ -n "$LEFTOVER" ]; then
  echo
  echo "[FAIL] Uninstall incomplete. Still present:" >&2
  for t in $LEFTOVER; do echo "  $t" >&2; done
  exit 1
fi

echo
echo "[OK] Verified: none of the removed paths remain."
echo "Uninstall complete."
if [ "$PURGE" = 1 ]; then
  echo "The Joystick desktop app itself is not removed by this script:"
  echo "  deb:      sudo apt-get remove joystick-gui"
  echo "  AppImage: delete the Joystick-*.AppImage file"
fi
