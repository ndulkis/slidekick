"""The presentation overlay: session status and gesture feedback in a small
window that floats over the slideshow. app.py runs this as its own process:

    python -m slidekick.overlay_window URL

The window never takes focus, so slide keystrokes still reach the
presentation app, and clicks pass through it to the slides underneath.
"""

import sys
from typing import Any

import webview

WIDTH, HEIGHT = 300, 160
# ponytail: fixed top-right corner of the main screen. Make it configurable
# (or follow the presenter-view screen) if it covers slide content.
MARGIN = 24


def float_over_slideshow_macos(window: webview.Window) -> None:
    import AppKit
    from PyObjCTools import AppHelper

    def apply() -> None:
        ns: Any = window.native  # an NSWindow; pywebview types it as None
        # Show on every Space, including a fullscreen slideshow's own Space.
        ns.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
            | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
            | AppKit.NSWindowCollectionBehaviorStationary
        )
        ns.setLevel_(AppKit.NSStatusWindowLevel)
        ns.setIgnoresMouseEvents_(True)

    AppHelper.callAfter(apply)


def float_over_slideshow_windows(window: webview.Window) -> None:
    import ctypes

    GWL_EXSTYLE = -20
    WS_EX_TRANSPARENT = 0x20  # clicks pass through (only on a layered window)
    WS_EX_TOOLWINDOW = 0x80  # no taskbar or Alt+Tab entry
    WS_EX_LAYERED = 0x80000
    LWA_ALPHA = 0x2

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    form: Any = window.native  # a WinForms Form; pywebview types it as None
    hwnd = form.Handle.ToInt32()
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    if not style & WS_EX_LAYERED:
        # A newly layered window draws nothing until it is given an opacity.
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)
        user32.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
    # pywebview's focus=False already sets WS_EX_NOACTIVATE (never takes focus).
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(
        hwnd, GWL_EXSTYLE, style | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
    )


def on_shown(window: webview.Window) -> None:
    if sys.platform == "darwin":
        float_over_slideshow_macos(window)
    elif sys.platform == "win32":
        float_over_slideshow_windows(window)


def main(url: str) -> None:
    screen = webview.screens[0]  # also loads the GUI backend
    if sys.platform == "darwin":
        import AppKit

        # No Dock icon. pywebview sets a regular app's policy when it loads.
        AppKit.NSApplication.sharedApplication().setActivationPolicy_(
            AppKit.NSApplicationActivationPolicyAccessory
        )
    # Typed Window | None, but only None for a window made after start().
    window: Any = webview.create_window(
        "SlideKick Overlay",
        url,
        width=WIDTH,
        height=HEIGHT,
        x=screen.width - WIDTH - MARGIN,
        y=MARGIN,
        frameless=True,
        on_top=True,
        transparent=True,
        focus=False,
        resizable=False,
        shadow=False,
    )
    # The native window exists once shown.
    window.events.shown += lambda: on_shown(window)
    webview.start()


if __name__ == "__main__":
    main(sys.argv[1])
