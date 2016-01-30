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

class Color:

	def __init__(self):
		pass


	def init_rgba(self, r, g, b, a):
		self._ro = r
		self._go = g
		self._bo = b
		self._ao = a;
		self._r = self._ro / 255.0
		self._g = self._go / 255.0
		self._b = self._bo / 255.0
		self._a = self._ao / 255.0

		self._opaque = False
		if (self._a == 1):
			self.opaque = True

		rgb_tup = ( self._ro, self._go, self._bo )
		self.hex = self.rgb_to_hex( rgb_tup )
		self.gColor = gtk.gdk.color_parse( self.hex )


	def init_gdk(self, col):
		self.init_hex( col.get_html() )


	def init_hex(self, hex):
		cTup = self.hex_to_rgb( hex )
		self.init_rgba( cTup[0], cTup[1], cTup[2], 255 )


	def get_int(self):
		return int(self._a * 255) + (int(self._b * 255) << 8) + (int(self._g * 255) << 16) + (int(self._r * 255) << 24)


	def rgb_to_hex(self, rgb_tup):
		hexcolor = '#%02x%02x%02x' % rgb_tup
		return hexcolor


	def hex_to_rgb(self, h):
		c = eval('0x' + h[1:])
		r = (c >> 16) & 0xFF
		g = (c >> 8) & 0xFF
		b = c & 0xFF
		return (int(r), int(g), int(b))


	def getCanvasColor(self):
		return str(self._ro) + "," + str(self._go) + "," + str(self._bo)