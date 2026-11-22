#!/usr/bin/env bash
# User-space OCaml + SDL2 toolchain for building bluddy/rails (no sudo).
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
CONDA="$HOME/miniconda3/bin/conda"
ENVNAME=railsdev

echo "== [1/4] conda env with SDL2 dev libs"
if [ ! -d "$HOME/miniconda3/envs/$ENVNAME" ]; then
  "$CONDA" create -y -n "$ENVNAME" --override-channels -c conda-forge \
    sdl2 sdl2_mixer pkg-config libffi gmp zlib
fi
ENVDIR="$HOME/miniconda3/envs/$ENVNAME"
export PKG_CONFIG_PATH="$ENVDIR/lib/pkgconfig:$ENVDIR/share/pkgconfig"
export PATH="$ENVDIR/bin:$PATH"
export LIBRARY_PATH="$ENVDIR/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"
export C_INCLUDE_PATH="$ENVDIR/include${C_INCLUDE_PATH:+:$C_INCLUDE_PATH}"
export LD_LIBRARY_PATH="$ENVDIR/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
pkg-config --modversion sdl2 SDL2_mixer

echo "== [2/4] opam binary"
if ! command -v opam >/dev/null; then
  mkdir -p "$HOME/.local/bin"
  curl -fsSL -o "$HOME/.local/bin/opam" \
    https://github.com/ocaml/opam/releases/download/2.3.0/opam-2.3.0-x86_64-linux
  chmod +x "$HOME/.local/bin/opam"
fi
opam --version

echo "== [3/4] opam init + OCaml 5.2 switch (compiles the compiler)"
if [ ! -d "$HOME/.opam" ]; then
  opam init --bare --disable-sandboxing --no-setup -y
fi
if ! opam switch list --short | grep -qx rails; then
  opam switch create rails 5.2.1 -y
fi
eval "$(opam env --switch=rails --set-switch)"
ocaml -version

echo "== [4/4] project dependencies (note: opam wants apt packages libsdl2-dev; conda provides them)"
cd "$(dirname "$0")/../.."
opam pin add tsdl-mixer "git+https://github.com/bluddy/tsdl-mixer.git#fix-windows-dll-search" -y --no-action || true
opam install . --deps-only --with-test -y --assume-depexts
echo "== DONE"
