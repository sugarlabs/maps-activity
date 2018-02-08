#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006, Red Hat, Inc.
# Copyright (C) 2007, One Laptop Per Child
# Copyright (c) 2008, Media Modifications Ltd.
# Copyright (c) 2016, Cristian García
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
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

import logging

from gi.repository import Gtk, Gdk
from gi.repository import GObject
from gi.repository import WebKit


class WebViewer(Gtk.ScrolledWindow):

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)

        self.browser = WebKit.WebView()
        self.add(self.browser)

    def load_uri(self, uri):
        self.browser.load_uri(uri)


class _PopupCreator(GObject.GObject):

    __gsignals__ = {
        'popup-created': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ([]))
    }

    def __init__(self, parent_window):
        GObject.GObject.__init__(self)

        logging.debug('Creating the popup widget')

        self._parent_window = parent_window

        self._dialog = Gtk.Window()
        self._dialog.set_resizable(True)

        self._dialog.realize()
        self._dialog.window.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        self._embed = Browser()  # Where it's from?
        self._vis_sid = self._embed.connect(
            'notify::visible', self._notify_visible_cb)
        self._dialog.add(self._embed)

    def _notify_visible_cb(self, embed, param):
        self._embed.disconnect(self._vis_sid)

        if self._embed.type == Browser.TYPE_POPUP or self._embed.is_chrome:
            logging.debug('Show the popup')
            self._embed.show()
            self._dialog.set_transient_for(self._parent_window)
            self._dialog.show()

        else:
            logging.debug('Open a new activity for the popup')
            self._dialog.remove(self._embed)
            self._dialog.destroy()
            self._dialog = None

            # FIXME We need a better way to handle this.
            # It seem like a pretty special case though, I doubt
            # other activities will need something similar.
            from webactivity import WebActivity
            from sugar3.activity import activityfactory
            from sugar3.activity.activityhandle import ActivityHandle
            handle = ActivityHandle(activityfactory.create_activity_id())
            activity = WebActivity(handle, self._embed)
            activity.show()

        self.emit('popup-created')

    def get_embed(self):
        return self._embed
