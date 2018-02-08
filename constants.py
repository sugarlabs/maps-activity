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

import os
from gettext import gettext as _

from gi.repository import Gtk

import sugar3.graphics.style
from sugar3.activity import activity

from instance import Instance
from color import Color
import utils


class Constants:

    VERSION = 8

    SERVICE = "org.laptop.Map"
    IFACE = SERVICE
    PATH = "/org/laptop/Map"
    activityId = None

    gfx_path = os.path.join(activity.get_bundle_path(), "gfx")
    html_path = os.path.join(activity.get_bundle_path(), "html")
    icons_path = os.path.join(activity.get_bundle_path(), "icons")

    istr_annotate = _("Edit")
    istr_search = _("Search")
    istr_search_address = _('Find:')
    istr_search_media = _("Tags:")
    istr_save_search = _("Save Search")
    istr_connecting = _("Connecting to Map Server")
    istr_zoom_in = _("Zoom In")
    istr_zoom_out = _("Zoom Out")
    istr_save_search = _("Save")
    istr_density = _("Density")
    istr_saved_map = _("Saved Map")
    istr_tag_map = _("Describe Map")
    istr_remove = _("Remove Map")
    istr_copy_to_clipboard = _("Copy to Clipboard")
    istr_add_media = _("Add Media")
    istr_add_info = _("Add Info")
    istr_delete_media = _("Delete")
    istr_web_media = _("Library")
    istr_measure = _("Measure")
    istr_static_maps = _("olpcMAP.net")
    istr_panoramio = _("Panoramio")
    istr_local_wiki = _("LocationWiki")
    istr_wiki_mapia = _("WikiMapia")
    istr_latitude = _("Latitude:")
    istr_longitude = _("Longitude:")
    istr_tags = _("Description:")
    istr_lang = _("lang=en")
    line_button = _("Add Line")
    poly_button = _("Add Shape")

    TYPE_PHOTO = 0
    TYPE_VIDEO = 1

    ui_dim_INSET = 4

    recd_album = "map"
    recd_lat = "lat"
    recd_lng = "lng"
    recd_datastore_id = "datastore"
    recd_info = "info"
    recd_map_item = "mapItem"
    recd_saved_map_item = "savedMap"
    recd_info_marker = "infoMarker"
    recd_icon = "icon"
    recd_zoom = "zoom"
    recd_notes = "notes"
    recd_map_img = "mapImg"
    recd_tags = "tags"
    recd_map_thumb_img = "mapThumbImg"
    recd_recd_id = "recdId"
    recd_recd_lat = "recdLat"
    recd_recd_lng = "recdLng"
    recd_density = "density"
    recd_line = "line"
    line_id = "lid"
    line_color = "lcolor"
    line_thick = "lthickness"
    line_pts = "lpts"
    map_lat = "lat"
    map_lng = "lng"
    map_zoom = "zoom"

    color_black = Color()
    color_black.init_rgba(0, 0, 0, 255)

    color_white = Color()
    color_white.init_rgba(255, 255, 255, 255)

    color_red = Color()
    color_red.init_rgba(255, 0, 0, 255)

    color_green = Color()
    color_green.init_rgba(0, 255, 0, 255)

    color_blue = Color()
    color_blue.init_rgba(0, 0, 255, 255)

    color_grey = Color()
    color_grey.init_gdk(sugar3.graphics.style.COLOR_BUTTON_GREY)
    color_bg = color_black

    def __init__(self, ca):
        self.activity_id = ca._activity_id
        self.north_img_clr, self.north_img_bw = self.load_svg_img(
            'map-icon-croseN.svg')
        self.south_img_clr, self.south_img_bw = self.load_svg_img(
            'map-icon-croseS.svg')
        self.east_omg_clr, self.east_img_bw = self.load_svg_img(
            'map-icon-croseE.svg')
        self.west_img_clr, self.west_img_bw = self.load_svg_img(
            'map-icon-croseW.svg')

        info_on_svg_path = os.path.join(
            self.__class__.icons_path, 'corner-info.svg')
        info_on_svg_file = open(info_on_svg_path, 'r')
        info_on_svg_data = info_on_svg_file.read()
        self.__class__.info_on_svg = utils.load_svg(
            info_on_svg_data, None, None)
        info_on_svg_file.close()

    def load_svg_img(self, fileName):
        svg_path = os.path.join(self.__class__.icons_path, fileName)
        svg_file = open(svg_path, 'r')
        svg_data = svg_file.read()
        svg_file.close()

        color_svg = utils.load_svg(
            svg_data,
            Instance.color_stroke.hex,
            Instance.color_fill.hex)
        color_pixbuf = color_svg.get_pixbuf()
        color_img = Gtk.Image.new_from_pixbuf(color_pixbuf)

        mono_svg = utils.load_svg(
            svg_data,
            self.__class__.color_grey.hex,
            self.__class__.color_white.hex)
        mono_pixbuf = mono_svg.get_pixbuf()
        mono_img = Gtk.Image()
        mono_img.set_from_pixbuf(mono_pixbuf)

        return [color_img, mono_img]
