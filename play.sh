#!/usr/bin/env bash
# Start the game in fullscreen (Alt+Enter toggles it while playing).
#   ./play.sh                 intro and menu, pick "Netherlands" in the area menu
#   ./play.sh --region 4      straight into the Netherlands
#   ./play.sh --no-audio      any other option of rails_run.exe works too
# Crisp pixels by default. The game's built-in CRT look (scanlines) is switched on with
#   ./play.sh --shader ega-1080p        (other shaders: see the shaders/ folder)
cd "$(dirname "$0")" || exit 1
source tools/dev/env.sh || exit 1
dune build ./src/rails_run.exe 2>/dev/null || { echo "Build failed: run 'dune build' to see why."; exit 1; }
# Some systems miss the GL symbols the game looks up at start-up (see tools/dev/README.md)
GL=/usr/lib/x86_64-linux-gnu/libGL.so.1
[ -e "$GL" ] && export LD_PRELOAD="$GL${LD_PRELOAD:+:$LD_PRELOAD}"
opts=(--fullscreen)
case " $* " in *" --shader "*|*" --no-shader "*) ;; *) opts+=(--no-shader) ;; esac
exec ./_build/default/src/rails_run.exe "${opts[@]}" "$@"
