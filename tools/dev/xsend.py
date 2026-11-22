#!/usr/bin/env python3
"""Developer helper: send key presses to ONE X11 window (by title) using XSendEvent.

Only the named window receives the events, so nothing can leak into other
applications.  Used to drive the SDL game window for screenshots.
Usage: xsend.py "Window Title" key [key ...]   (X keysym names, e.g. Return Down space)
"""
import ctypes, subprocess, sys, re, time
from ctypes import c_int, c_uint, c_ulong, c_long, c_void_p, byref

X = ctypes.CDLL("libX11.so.6")
X.XOpenDisplay.restype = c_void_p
X.XDefaultRootWindow.restype = c_ulong
X.XStringToKeysym.restype = c_ulong
X.XKeysymToKeycode.restype = c_uint


class XKeyEvent(ctypes.Structure):
    _fields_ = [("type", c_int), ("serial", c_ulong), ("send_event", c_int), ("display", c_void_p),
                ("window", c_ulong), ("root", c_ulong), ("subwindow", c_ulong), ("time", c_ulong),
                ("x", c_int), ("y", c_int), ("x_root", c_int), ("y_root", c_int), ("state", c_uint),
                ("keycode", c_uint), ("same_screen", c_int)]


class XEvent(ctypes.Union):
    _fields_ = [("type", c_int), ("xkey", XKeyEvent), ("pad", c_long * 24)]


def find_window(title):
    out = subprocess.run(["xwininfo", "-root", "-tree"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if title in line:
            m = re.search(r"(0x[0-9a-f]+)", line)
            if m:
                return int(m.group(1), 16)
    raise SystemExit("window not found: " + title)


def main():
    title, keys = sys.argv[1], sys.argv[2:]
    win = find_window(title)
    dpy = X.XOpenDisplay(None)
    root = X.XDefaultRootWindow(dpy)
    for name in keys:
        ks = X.XStringToKeysym(name.encode())
        kc = X.XKeysymToKeycode(dpy, ks)
        for etype, mask in ((2, 1), (3, 2)):  # KeyPress/KeyPressMask, KeyRelease/KeyReleaseMask
            ev = XEvent()
            ev.xkey = XKeyEvent(etype, 0, 1, dpy, win, root, 0, 0, 1, 1, 1, 1, 0, kc, 1)
            X.XSendEvent(dpy, win, True, mask, byref(ev))
            X.XFlush(dpy)
            time.sleep(0.05)
        time.sleep(0.25)


main()
