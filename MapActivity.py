#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from sugar3.activity.activity import Activity

from toolbar import MapToolbarBox


class MapActivity(Activity):

    def __init__(self, handle):
        Activity.__init__(self, handle)

        self.setup_toolbar()

        self.show_all()

    def setup_toolbar(self):
        toolbarbox = MapToolbarBox(self)
        self.set_toolbar_box(toolbarbox)

        toolbarbox.show_all()
