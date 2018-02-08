#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, Cristian García.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from gi.repository import Gtk
from gi.repository import Gdk


class P5(Gtk.DrawingArea):

    def __init__(self, button=False):
        Gtk.DrawingArea.__init__(self)

        self.connect("draw", self.draw_cb)

        if (button):
            self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                            Gdk.EventMask.BUTTON_RELEASE_MASK |
                            Gdk.EventMask.POINTER_MOTION_MASK)

            self.connect("button-press_event", self._button_press)

    def draw_cb(self, widget, ctx):
        rect = self.get_allocation()

        # set a clip region for the expose event
        ctx.rectangle(0, 0, rect.width, rect.height)
        ctx.clip()

        self.redraw(ctx, rect.width, rect.height)

    def redraw_canvas(self):
        # called from update
        if self.get_window():
            alloc = self.get_allocation()
            self.queue_draw_area(0, 0, alloc.width, alloc.height)

    def redraw(self, ctx, width, height):
        self.queue_draw_area(0, 0, width, height)

    def update(self):
        # paint thread -- call redraw_canvas, which calls expose
        self.redraw_canvas()

    def fill_rect(self, ctx, col, w, h):
        self.set_color(ctx, col)

        ctx.line_to(0, 0)
        ctx.line_to(w, 0)
        ctx.line_to(w, h)
        ctx.line_to(0, h)
        ctx.close_path()

        ctx.fill()

    def set_color(self, ctx, col):
        if not col._opaque:
            ctx.set_source_rgba(col._r, col._g, col._b, col._a)

        else:
            ctx.set_source_rgb(col._r, col._g, col._b)

    def _button_press(self, widget, event):
        self.fire_button()

    def fire_button(self):
        # for extending
        pass
