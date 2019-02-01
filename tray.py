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

from gi.repository import Gtk
from gi.repository import GObject

from sugar3.graphics import style
from sugar3.graphics.icon import Icon


_PREVIOUS_PAGE = 0
_NEXT_PAGE = 1


class _TrayViewport(Gtk.Viewport):

    __gproperties__ = {
        'can-scroll': (bool, None, None, False, GObject.PARAM_READABLE)
    }

    def __init__(self, orientation):
        self.orientation = orientation
        self._can_scroll = False

        Gtk.Viewport.__init__(self)

        self.set_shadow_type(Gtk.ShadowType.NONE)

        self.traybar = Gtk.Toolbar()
        self.traybar.set_orientation(orientation)
        self.traybar.set_show_arrow(False)
        self.add(self.traybar)

        self.connect('size-allocate', self._size_allocate_cb)

        self.show_all()

    def scroll(self, direction):
        if direction == _PREVIOUS_PAGE:
            self._scroll_previous()

        elif direction == _NEXT_PAGE:
            self._scroll_next()

    def _scroll_next(self):
        if self.orientation == Gtk.Orientation.HORIZONTAL:
            adj = self.get_hadjustment()
            new_value = adj.value + self.allocation.width
            adj.value = min(new_value, adj.upper - self.allocation.width)

        else:
            adj = self.get_vadjustment()
            new_value = adj.value + self.allocation.height
            adj.value = min(new_value, adj.upper - self.allocation.height)

    def _scroll_to_end(self):
        if self.orientation == Gtk.Orientation.HORIZONTAL:
            adj = self.get_hadjustment()
            adj.value = adj.upper  # - self.allocation.width

        else:
            adj = self.get_vadjustment()
            adj.value = adj.upper - self.allocation.height

    def _scroll_previous(self):
        if self.orientation == Gtk.Orientation.HORIZONTAL:
            adj = self.get_hadjustment()
            new_value = adj.value - self.allocation.width
            adj.value = max(adj.lower, new_value)

        else:
            adj = self.get_vadjustment()
            new_value = adj.value - self.allocation.height
            adj.value = max(adj.lower, new_value)

    def do_size_request(self, requisition):
        child_requisition = self.child.size_request()
        if self.orientation == Gtk.Orientation.HORIZONTAL:
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
        if self.orientation == Gtk.Orientation.HORIZONTAL:
            can_scroll = bar_requisition.width > allocation.width

        else:
            can_scroll = bar_requisition.height > allocation.height

        if can_scroll != self._can_scroll:
            self._can_scroll = can_scroll
            self.notify('can-scroll')


class _TrayScrollButton(Gtk.Button):

    def __init__(self, icon_name, scroll_direction):
        Gtk.Button.__init__(self)

        self._viewport = None

        self._scroll_direction = scroll_direction

        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_size_request(style.GRID_CELL_SIZE, style.GRID_CELL_SIZE)

        icon = Icon(icon_name=icon_name, pixel_size=Gtk.IconSize.SMALL_TOOLBAR)
        self.set_image(icon)
        icon.show()

        self.connect('clicked', self._clicked_cb)

    def set_viewport(self, viewport):
        self._viewport = viewport
        self._viewport.connect(
            'notify::can-scroll',
            self._viewport_can_scroll_changed_cb)

    def _viewport_can_scroll_changed_cb(self, viewport, pspec):
        self.set_sensitive(self._viewport.props.can_scroll)

    def _clicked_cb(self, button):
        self._viewport.scroll(self._scroll_direction)

    viewport = property(fset=set_viewport)


class HTray(Gtk.VBox):

    def __init__(self, **kwargs):
        Gtk.VBox.__init__(self, **kwargs)

        separator = Gtk.HBox()
        separator.set_size_request(1, 1)
        separator.set_margin_bottom(1)
        self.pack_start(separator, False, False, 0)

        hbox = Gtk.HBox()
        self.pack_start(hbox, True, True, 0)

        self.scroll_left = _TrayScrollButton('go-left', _PREVIOUS_PAGE)
        self.scroll_left_event = Gtk.EventBox()
        self.scroll_left_event.add(self.scroll_left)
        self.scroll_left_event.set_size_request(55, -1)
        hbox.pack_start(self.scroll_left_event, False, False, 0)

        self.viewport = _TrayViewport(Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(self.viewport, True, True, 0)
        self.viewport.show()

        self.scroll_right = _TrayScrollButton('go-right', _NEXT_PAGE)
        self.scroll_right_event = Gtk.EventBox()
        self.scroll_right_event.add(self.scroll_right)
        self.scroll_right_event.set_size_request(55, -1)
        hbox.pack_start(self.scroll_right_event, False, False, 0)

        self.scroll_left.set_focus_on_click(False)
        # self.scroll_left_event.modify_bg(Gtk.StateType.NORMAL, sugar3.graphics.style.COLOR_TOOLBAR_GREY.get_gdk_color())
        # self.scroll_left.modify_bg(Gtk.StateType.ACTIVE, sugar3.graphics.style.COLOR_BUTTON_GREY.get_gdk_color())

        self.scroll_right.set_focus_on_click(False)
        # self.scroll_right_event.modify_bg(Gtk.StateType.NORMAL, sugar3.graphics.style.COLOR_TOOLBAR_GREY.get_gdk_color())
        # self.scroll_right.modify_bg(Gtk.StateType.ACTIVE, sugar3.graphics.style.COLOR_BUTTON_GREY.get_gdk_color())

        self.scroll_left.viewport = self.viewport
        self.scroll_right.viewport = self.viewport

        self.connect_after("size-allocate", self._sizeAllocateCb)

    def _sizeAllocateCb(self, widget, event):
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
