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
from gi.repository import GObject
from gi.repository import GdkPixbuf

from sugar3.graphics.palette import Palette
from sugar3.graphics.tray import TrayButton

from constants import Constants
import utils


class SavedButton(TrayButton, GObject.GObject):

    def __init__(self, ui, savedmap_data):
        TrayButton.__init__(self)

        self.ui = ui
        self.data = savedmap_data

        img = self.get_img()
        self.set_icon_widget(img)

        self.setup_rollover_options()

    def getImg(self):
        pb = GdkPixbuf.Pixbuf.new_from_file(self.data.thumb_path)

        img = Gtk.Image()
        img.set_from_pixbuf(pb)
        img.show()

        return img

    def set_button_clicked_id(self, id):
        self.BUTT_CLICKED_ID = id

    def get_button_clicked_id(self):
        return self.BUTT_CLICKED_ID

    def setup_rollover_options(self):
        palette = Palette(Constants.istr_saved_map)
        self.set_palette(palette)

        self.tag_menu_item = Gtk.MenuItem(Constants.istr_tag_map)
        self.ACTIVATE_TAG_ID = self.tag_menu_item.connect(
            'activate', self._tag_cb)
        palette.menu.append(self.tag_menu_item)
        self.tag_menu_item.show()

        self.rem_menu_item = Gtk.MenuItem(Constants.istr_remove)
        self.ACTIVATE_REMOVE_ID = self.rem_menu_item.connect(
            'activate', self._item_remove_cb)
        palette.menu.append(self.rem_menu_item)
        self.rem_menu_item.show()

        self.copy_menu_item = Gtk.MenuItem(Constants.istr_copy_to_clipboard)
        self.ACTIVATE_COPY_ID = self.copy_menu_item.connect(
            'activate', self._item_copy_to_clipboard_cb)
        self.get_palette().menu.append(self.copy_menu_item)
        self.copy_menu_item.show()

    def cleanUp(self):
        self.rem_menu_item.disconnect(self.ACTIVATE_REMOVE_ID)
        self.copy_menu_item.disconnect(self.ACTIVATE_COPY_ID)
        self.tag_menu_item.disconnect(self.ACTIVATE_TAG_ID)

    def _tagCb(self, widget):
        self.ui.show_search_result_tags(self.data)

    def _itemRemoveCb(self, widget):
        self.ui.remove_thumb(self.data)

    def _itemCopyToClipboardCb(self, widget):
        self.ui.copy_to_clipboard(self.data)
