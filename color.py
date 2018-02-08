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

from gi.repository import Gdk


class Color:

    def __init__(self):
        pass

    def init_rgba(self, r, g, b, a):
        self._ro = r
        self._go = g
        self._bo = b
        self._ao = a
        self._r = self._ro / 255.0
        self._g = self._go / 255.0
        self._b = self._bo / 255.0
        self._a = self._ao / 255.0

        self._opaque = False
        if (self._a == 1):
            self.opaque = True

        rgb_tup = (self._ro, self._go, self._bo)
        self.hex = self.rgb_to_hex(rgb_tup)
        self.g_color = Gdk.Color.parse(self.hex)[1]

    def init_gdk(self, col):
        self.init_hex(col.get_html())

    def init_hex(self, hex):
        c_tup = self.hex_to_rgb(hex)
        self.init_rgba(c_tup[0], c_tup[1], c_tup[2], 255)

    def get_int(self):
        return int(self._a * 255) + (int(self._b * 255) << 8) + \
            (int(self._g * 255) << 16) + (int(self._r * 255) << 24)

    def rgb_to_hex(self, rgb_tup):
        hexcolor = '#%02x%02x%02x' % rgb_tup
        return hexcolor

    def hex_to_rgb(self, h):
        c = eval('0x' + h[1:])
        r = (c >> 16) & 0xFF
        g = (c >> 8) & 0xFF
        b = c & 0xFF
        return (int(r), int(g), int(b))

    def get_canvas_color(self):
        return str(self._ro) + "," + str(self._go) + "," + str(self._bo)
