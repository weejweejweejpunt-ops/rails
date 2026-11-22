# source this to get the Rails dev toolchain (user-space, no sudo): conda env "railsdev" (SDL2) + opam switch "rails" (OCaml 5.2)
export PATH="$HOME/.local/bin:$PATH"
ENVDIR="$HOME/miniconda3/envs/railsdev"
export PKG_CONFIG_PATH="$ENVDIR/lib/pkgconfig:$ENVDIR/share/pkgconfig"
export PATH="$ENVDIR/bin:$PATH"
export LIBRARY_PATH="$ENVDIR/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"
export C_INCLUDE_PATH="$ENVDIR/include${C_INCLUDE_PATH:+:$C_INCLUDE_PATH}"
export LD_LIBRARY_PATH="$ENVDIR/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
eval "$(opam env --switch=rails --set-switch)"
