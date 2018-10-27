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

import cairo

from gi.repository import GLib

from p5 import P5
from constants import Constants


class PhotoCanvas(P5):

    def __init__(self):
        P5.__init__(self)

        self.img = None
        self.draw_img = None
        self.SCALING_IMG_ID = 0
        self.cacheWid = -1

        # self.modify_bg(Gtk.StateType.NORMAL, Constants.colorBlack.gColor)
        # self.modify_bg(Gtk.StateType.INSENSITIVE, Constants.colorBlack.gColor)

    def redraw(self, ctx, w, h):
        self.fill_rect(ctx, Constants.colorBlack, w, h)

        if self.img is not None:
            if w == self.img.get_width():
                self.cacheWid == w
                self.draw_img = self.img

            # only scale images when you need to, otherwise you're wasting
            # cycles, fool!
            if self.cacheWid != w:
                if self.SCALING_IMG_ID == 0:
                    self.draw_img = None
                    self.SCALING_IMG_ID = GLib.idle_add(
                        self.resize_image, w, h)

            if self.draw_img is not None:
                # center the image based on the image size, and w & h
                ctx.set_source_surface(self.draw_img,
                                       (w / 2) - (self.draw_img.get_width() / 2),
                                       (h / 2) - (self.draw_img.get_height() / 2))
                ctx.paint()

            self.cacheWid = w

    def setImage(self, img):
        self.cacheWid = -1
        self.img = img
        self.draw_img = None
        self.queue_draw()

    def resize_image(self, w, h):
        self.SCALING_IMG_ID = 0
        if (self.img is None):
            return

        # use image size in case 640 no more
        scaleImg = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        sCtx = cairo.Context(scaleImg)
        sScl = (w + 0.0) / (self.img.get_width() + 0.0)
        sCtx.scale(sScl, sScl)
        sCtx.set_source_surface(self.img, 0, 0)
        sCtx.paint()
        self.draw_img = scaleImg
        self.cacheWid = w
        self.queue_draw()
