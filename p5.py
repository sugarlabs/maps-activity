# Copyright (c) 2008, Media Modifications Ltd.

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

import gtk
from gtk import gdk
import gobject
import cairo
import math


class P5(gtk.DrawingArea):
	def __init__(self, button=False):
		super(P5, self).__init__()
		self.connect("expose_event", self.expose)
		if (button):
			self.add_events(gdk.BUTTON_PRESS_MASK | gdk.BUTTON_RELEASE_MASK | gdk.POINTER_MOTION_MASK)
			self.connect("button_press_event", self._buttonPress)


	def expose(self, widget, event):
		ctx = widget.window.cairo_create()

		# set a clip region for the expose event
		ctx.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
		ctx.clip()

		rect = widget.allocation
		self.draw( ctx, rect.width, rect.height )


	def redraw_canvas(self):
		#called from update
		if self.window:
			alloc = self.get_allocation()
			self.queue_draw_area(0, 0, alloc.width, alloc.height)
			self.window.process_updates(True)


	def update(self):
		#paint thread -- call redraw_canvas, which calls expose
		self.redraw_canvas()


	def fillRect( self, ctx, col, w, h ):
		self.setColor( ctx, col )

		ctx.line_to(0, 0)
		ctx.line_to(w, 0)
		ctx.line_to(w, h)
		ctx.line_to(0, h)
		ctx.close_path()

		ctx.fill()


	def setColor( self, ctx, col ):
		if (not col._opaque):
			ctx.set_source_rgba( col._r, col._g, col._b, col._a )
		else:
			ctx.set_source_rgb( col._r, col._g, col._b )


	def _buttonPress(self, widget, event):
		self.fireButton()


	def fireButton( self ):
		#for extending
		pass