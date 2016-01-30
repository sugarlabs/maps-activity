#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gi.repository import Gtk

from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.toolbarbox import ToolbarBox


def make_separator(expand=False):
    sep = Gtk.SeparatorToolItem()
    sep.props.draw = not expand
    sep.set_expand(expand)
    return sep


class MapToolbarBox(ToolbarBox):

    def __init__(self, activity):
        ToolbarBox.__init__(self)

        activity_button = ActivityToolbarButton(activity)
        self.toolbar.insert(activity_button, -1)

        self.toolbar.insert(make_separator(True), -1)

        stop_button = StopButton(activity)
        self.toolbar.insert(stop_button, -1)

