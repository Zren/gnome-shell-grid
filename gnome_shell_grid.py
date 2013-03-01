#!/usr/bin/env python

import logging
import re

import Xlib
import Xlib.display

from Xlib import X, XK, Xutil

import gtk
import wnck


class Opts(object):

    """ Keyboard mapping """
    keymap = {
        '<Control><Alt>KP_5':       'put_center',
        '<Control><Alt>KP_4':       'put_left',
        '<Shift><Control><Alt>h':   'put_left',
        '<Control><Alt>KP_6':       'put_right',
        '<Shift><Control><Alt>l':   'put_right',
        '<Control><Alt>KP_8':       'put_top',
        '<Shift><Control><Alt>k':   'put_top',
        '<Control><Alt>KP_2':       'put_bottom',
        '<Shift><Control><Alt>j':   'put_bottom',
        '<Control><Alt>KP_7':       'put_top_left',
        '<Shift><Control><Alt>u':   'put_top_left',
        '<Control><Alt>KP_9':       'put_top_right',
        '<Shift><Control><Alt>i':   'put_top_right',
        '<Control><Alt>KP_1':       'put_bottom_left',
        '<Shift><Control><Alt>n':   'put_bottom_left',
        '<Control><Alt>KP_3':       'put_bottom_right',
        '<Shift><Control><Alt>m':   'put_bottom_right',
    }

    """ Panel sizes for each monitor. """
    panels = [
        {},  # monitor 0
    ]

    """
    How close to match the current window position when cycling through
    different placements.
    """
    pos_match_epsilon = 300


OPTS = Opts()


def put_center(w, h):
    return [
        (0, 0, w, h),
        (w * 1/3., 0, w * 1/3., h),
    ]

def put_left(w, h):
    return [
        (0, 0, w * 1/2., h),
        (0, 0, w * 1/3., h),
        (0, 0, w * 2/3., h),
    ]

def put_right(w, h):
    return [
        (w * 1/2., 0, w * 1/2., h),
        (w * 2/3., 0, w * 1/3., h),
        (w * 1/3., 0, w * 2/3., h),
    ]

def put_top(w, h):
    return [
        (0, 0, w, h * 1/2.),
        (w * 1/3., 0, w * 1/3., h * 1/2.),
    ]

def put_bottom(w, h):
    return [
        (0, h * 1/2., w, h * 1/2.),
        (w * 1/3., h * 1/2., w * 1/3., h * 1/2.),
    ]

def put_top_left(w, h):
    return [
        (0, 0, w * 1/2., h * 1/2.),
        (0, 0, w * 1/3., h * 1/2.),
        (0, 0, w * 2/3., h * 1/2.),
    ]

def put_top_right(w, h):
    return [
        (w * 1/2., 0, w * 1/2., h * 1/2.),
        (w * 2/3., 0, w * 1/3., h * 1/2.),
        (w * 1/3., 0, w * 2/3., h * 1/2.),
    ]

def put_bottom_left(w, h):
    return [
        (0, h * 1/2., w * 1/2., h * 1/2.),
        (0, h * 1/2., w * 1/3., h * 1/2.),
        (0, h * 1/2., w * 2/3., h * 1/2.),
    ]

def put_bottom_right(w, h):
    return [
        (w * 1/2., h * 1/2., w * 1/2., h * 1/2.),
        (w * 2/3., h * 1/2., w * 1/3., h * 1/2.),
        (w * 1/3., h * 1/2., w * 2/3., h * 1/2.),
    ]

put_funcs = {
    'put_center': put_center,
    'put_left': put_left,
    'put_right': put_right,
    'put_top': put_top,
    'put_bottom': put_bottom,
    'put_top_left': put_top_left,
    'put_top_right': put_top_right,
    'put_bottom_left': put_bottom_left,
    'put_bottom_right': put_bottom_right,
}


KEY_MOD_RE = re.compile('<([^>]+)>', re.I)
KEY_MASKS = {
    'control': X.ControlMask,
    'alt': X.Mod1Mask,
    'shift': X.ShiftMask,
    'super': X.Mod4Mask,
}

def keystr_to_sym_mask(s):
    """
    >>> keystr_to_sym_mask('<Control><Alt>KP_3')
    (65459, 12)
    >>> _ == (XK.XK_KP_3, X.Mod1Mask | X.ControlMask)
    True
    >>>
    """
    mask = 0
    sym_start = 0
    for m in KEY_MOD_RE.finditer(s):
        mask |= KEY_MASKS[m.group(1).lower()]
        sym_start = max(sym_start, m.end())
    keysym = XK.string_to_keysym(s[sym_start:])
    if not keysym:
        logging.warning('Ignoring Unknown keysym %r in key binding %r',
                        s[sym_start:], s)
    return (keysym, mask)


class Placement(object):
    __slots__ = ('x', 'y', 'w', 'h', 'maximize')

    def __init__(self, x, y, w, h, maximize=False):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.maximize = maximize


def check_num_lock(*args):
    display = Xlib.display.Display()
    gkc = display.get_keyboard_control()
    if gkc.led_mask & 2 == 2:
        logging.warning('NumLock is on; your bindings may not work')


def adjust_monitor_geometry_for_panels(g, panels):
    """
    Adjusts screen geometry to account for panels.
    @param[out] g - Rectangle object to be modified.
    """
    if 'top' in panels:
        g.y += panels['top']
        g.height -= panels['top']
    if 'bottom' in panels:
        g.height -= panels['bottom']
    if 'left' in panels:
        g.x += panels['left']
        g.width -= panels['left']
    if 'right' in panels:
        g.width -= panels['right']


def setup_plist_map(gscreen):
    """
    @param[in] gscreen Usually gtk.gdk.screen_get_default().
    @return map of 'put_xxx' to list of possible positions for each monitor.
    { 'put_left': [ [Placement(), Placement()], # mon 0 positions
                    [Placement(), Placement()], # mon 1 positions ]
    """
    out = {}
    for i in range(gscreen.get_n_monitors()):
        g = gscreen.get_monitor_geometry(i)
        try:
            panels = OPTS.panels[i]
        except IndexError:
            panels = {}
        logging.info('Monitor %s (%s, %s, %s, %s) panels = %r', i,
                     g.x, g.y, g.width, g.height, panels)
        adjust_monitor_geometry_for_panels(g, panels)
        for name, put_func in put_funcs.iteritems():
            plist = []
            xywh_list = put_func(g.width, g.height)
            for x, y, w, h in xywh_list:
                p = Placement(int(g.x + x),
                              int(g.y + y),
                              int(w), int(h),
                              maximize=(w == g.width and h == g.height))
                plist.append(p)
            out.setdefault(name, []).append(plist)
    return out


def get_next_placement(plist, wextents):
    """
    @param[in] plist - List of Placement()'s.
    @param[in] wextents Window x, y, width, height.
    """
    # if the window is already placed, find the placed position
    i = 0
    for p in plist:
        if (    abs(wextents.x - p.x) ** 2 +
                abs(wextents.y - p.y) ** 2 +
                abs(wextents.width - p.w) ** 2 +
                abs(wextents.height - p.h) ** 2) < OPTS.pos_match_epsilon:
            break
        i += 1
    else:
        # random window placement, use the first position
        return plist[0]
    return plist[(i + 1) % len(plist)]


def run_idle():
    while gtk.events_pending():
        gtk.main_iteration()


def main():
    import sys
    FORMAT = '%(asctime)-15s: %(message)s'
    level = logging.INFO
    if '-v' in sys.argv:
        level = logging.DEBUG
    logging.basicConfig(format=FORMAT, level=level)

    display = Xlib.display.Display()
    root = display.screen().root
    root.change_attributes(event_mask = X.KeyReleaseMask)

    wscreen = wnck.screen_get_default()
    wscreen.force_update()

    gscreen = gtk.gdk.screen_get_default()
    name_to_plists = setup_plist_map(gscreen)

    keysym_to_plists = {}
    for keystr, put_type in OPTS.keymap.iteritems():
        keysym, keymask = keystr_to_sym_mask(keystr)
        if not keysym:
            continue
        logging.debug('%r (keysym %r, keymask %r) => %s', keystr, keysym,
                      keymask, put_type)
        keysym_to_plists[keysym] = name_to_plists[put_type]
        root.grab_key(display.keysym_to_keycode(keysym), keymask, True,
                      X.GrabModeAsync, X.GrabModeAsync)

    check_num_lock()
    while True:
        event = root.display.next_event()
        run_idle()
        if event.type != X.KeyRelease:
            continue

        run_idle()
        for i in range(4):
            try:
                keysym = display.keycode_to_keysym(event.detail, i)
                plists = keysym_to_plists[keysym]
                break
            except KeyError:
                continue
        else:
            logging.warning('got unhandled event %r', event)
            continue

        gw = gscreen.get_active_window()
        if gw is None:
            continue
        mon_idx = gscreen.get_monitor_at_window(gw)
        plist = plists[mon_idx]
        wextents = gw.get_frame_extents()
        p = get_next_placement(plist, wextents)

        ww = wscreen.get_active_window()
        logging.debug('%r (%d, %d, %d, %d) -> (%d, %d, %d, %d)',
                      ww.get_name(), wextents.x, wextents.y, wextents.width,
                      wextents.height, p.x, p.y, p.w, p.h)
        if ww is None:
            continue

        if not p.maximize:
            ww.unmaximize()
        # ww.set_geometry(0, 15, p.x, p.y, p.w, p.h)
        # workaround for set_geometry() not incorporating window decorations.
        dg = ww.get_client_window_geometry()
        ww.set_geometry(0, 15, p.x + (wextents.x - dg[0]),
                        p.y + (wextents.y - dg[1]), p.w, p.h)
        if p.maximize:
            ww.maximize()
        run_idle()


if __name__ == "__main__":
    main()
