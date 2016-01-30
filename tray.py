# Copyright (C) 2007, One Laptop Per Child
# Copyright (c) 2008, Media Modifications Ltd.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import gobject
import gtk
import hippo

import sugar
from sugar.graphics import style
from sugar.graphics.palette import Palette, ToolInvoker
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.icon import Icon

from constants import Constants

_PREVIOUS_PAGE = 0
_NEXT_PAGE = 1

class _TrayViewport(gtk.Viewport):
    __gproperties__ = {
        'can-scroll' : (bool, None, None, False,
                        gobject.PARAM_READABLE),
    }

    def __init__(self, orientation):
        self.orientation = orientation
        self._can_scroll = False

        gobject.GObject.__init__(self)

        self.set_shadow_type(gtk.SHADOW_NONE)

        self.traybar = gtk.Toolbar()
        self.traybar.set_orientation(orientation)
        self.traybar.set_show_arrow(False)
        self.add(self.traybar)
        self.traybar.show()

        self.connect('size_allocate', self._size_allocate_cb)

    def scroll(self, direction):
        if direction == _PREVIOUS_PAGE:
            self._scroll_previous()
        elif direction == _NEXT_PAGE:
            self._scroll_next()

    def _scroll_next(self):
        if self.orientation == gtk.ORIENTATION_HORIZONTAL:
            adj = self.get_hadjustment()
            new_value = adj.value + self.allocation.width
            adj.value = min(new_value, adj.upper - self.allocation.width)
        else:
            adj = self.get_vadjustment()
            new_value = adj.value + self.allocation.height
            adj.value = min(new_value, adj.upper - self.allocation.height)

    def _scroll_to_end(self):
        if self.orientation == gtk.ORIENTATION_HORIZONTAL:
            adj = self.get_hadjustment()
            adj.value = adj.upper# - self.allocation.width
        else:
            adj = self.get_vadjustment()
            adj.value = adj.upper - self.allocation.height

    def _scroll_previous(self):
        if self.orientation == gtk.ORIENTATION_HORIZONTAL:
            adj = self.get_hadjustment()
            new_value = adj.value - self.allocation.width
            adj.value = max(adj.lower, new_value)
        else:
            adj = self.get_vadjustment()
            new_value = adj.value - self.allocation.height
            adj.value = max(adj.lower, new_value)

    def do_size_request(self, requisition):
        child_requisition = self.child.size_request()
        if self.orientation == gtk.ORIENTATION_HORIZONTAL:
            requisition[0] = 0
            requisition[1] = child_requisition[1]
        else:
            requisition[0] = child_requisition[0]
            requisition[1] = 0

    def do_get_property(self, pspec):
        if pspec.name == 'can-scroll':
            return self._can_scroll

    def _size_allocate_cb(self, viewport, allocation):
        bar_requisition = self.traybar.get_child_requisition()
        if self.orientation == gtk.ORIENTATION_HORIZONTAL:
            can_scroll = bar_requisition[0] > allocation.width
        else:
            can_scroll = bar_requisition[1] > allocation.height

        if can_scroll != self._can_scroll:
            self._can_scroll = can_scroll
            self.notify('can-scroll')

class _TrayScrollButton(gtk.Button):
    def __init__(self, icon_name, scroll_direction):
        gobject.GObject.__init__(self)

        self._viewport = None

        self._scroll_direction = scroll_direction

        self.set_relief(gtk.RELIEF_NONE)
        self.set_size_request(style.GRID_CELL_SIZE, style.GRID_CELL_SIZE)

        icon = Icon(icon_name = icon_name,
                    icon_size=gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.set_image(icon)
        icon.show()

        self.connect('clicked', self._clicked_cb)

    def set_viewport(self, viewport):
        self._viewport = viewport
        self._viewport.connect('notify::can-scroll',
                               self._viewport_can_scroll_changed_cb)

    def _viewport_can_scroll_changed_cb(self, viewport, pspec):
        #self.props.visible = self._viewport.props.can_scroll
        self.set_sensitive(self._viewport.props.can_scroll)

    def _clicked_cb(self, button):
        self._viewport.scroll(self._scroll_direction)

    viewport = property(fset=set_viewport)

class HTray(gtk.VBox):
    def __init__(self, **kwargs):
        gobject.GObject.__init__(self, **kwargs)

        separator = hippo.Canvas()
        box = hippo.CanvasBox(
                    border_color=Constants.colorWhite.get_int(),
                    background_color=Constants.colorWhite.get_int(),
                    box_height=1,
                    border_bottom=1)
        separator.set_root(box)
        self.pack_start(separator, False)

        hbox = gtk.HBox()
        self.pack_start(hbox)

        self.scroll_left = _TrayScrollButton('go-left', _PREVIOUS_PAGE)
        self.scroll_left_event = gtk.EventBox()
        self.scroll_left_event.add(self.scroll_left)
        self.scroll_left_event.set_size_request(55, -1)
        hbox.pack_start(self.scroll_left_event, False)

        self.viewport = _TrayViewport(gtk.ORIENTATION_HORIZONTAL)
        hbox.pack_start(self.viewport)
        self.viewport.show()

        self.scroll_right = _TrayScrollButton('go-right', _NEXT_PAGE)
        self.scroll_right_event = gtk.EventBox()
        self.scroll_right_event.add(self.scroll_right)
        self.scroll_right_event.set_size_request(55, -1)
        hbox.pack_start(self.scroll_right_event, False)

        self.scroll_left.set_focus_on_click(False)
        self.scroll_left_event.modify_bg(gtk.STATE_NORMAL, sugar.graphics.style.COLOR_TOOLBAR_GREY.get_gdk_color())
        self.scroll_left.modify_bg(gtk.STATE_ACTIVE, sugar.graphics.style.COLOR_BUTTON_GREY.get_gdk_color())

        self.scroll_right.set_focus_on_click(False)
        self.scroll_right_event.modify_bg(gtk.STATE_NORMAL, sugar.graphics.style.COLOR_TOOLBAR_GREY.get_gdk_color())
        self.scroll_right.modify_bg(gtk.STATE_ACTIVE, sugar.graphics.style.COLOR_BUTTON_GREY.get_gdk_color())

        self.scroll_left.viewport = self.viewport
        self.scroll_right.viewport = self.viewport

        self.connect_after("size-allocate", self._sizeAllocateCb)

    def _sizeAllocateCb(self, widget, event ):
        self.viewport.notify('can-scroll')

    def get_children(self):
        return self.viewport.traybar.get_children()

    def add_item(self, item, index=-1):
        self.viewport.traybar.insert(item, index)

    def remove_item(self, item):
        self.viewport.traybar.remove(item)

    def get_item_index(self, item):
        return self.viewport.traybar.get_item_index(item)

    def scroll_to_end(self):
        self.viewport._scroll_to_end()