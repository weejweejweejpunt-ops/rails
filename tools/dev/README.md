# Developer helpers

* `setup_toolchain.sh` - installs OCaml 5.2 (opam) and SDL2 (conda) in your home directory, no sudo.
  Needs `~/miniconda3`. Afterwards `source tools/dev/env.sh` in every new shell, then `dune build`.
* `rtpic.py` - Python decoder for the original `.PIC` images and `CITIES*.DTA` files (analysis only).
* `xsend.py` - sends key presses to one X11 window by title (XSendEvent), so the SDL window can be driven
  for screenshots: start the game with `SDL_VIDEODRIVER=x11`, then
  `python3 tools/dev/xsend.py "Open Railroad Tycoon" space Return Down` and `import -window <id> shot.png`.
* On some systems the game, `dump_map.exe` and `dune runtest` fail with "undefined symbol: glGenTextures":
  run them with `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libGL.so.1`.
