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

import base64
import re
import os
import cairo
import gc
from hashlib import md5
import time
from time import strftime

from gi.repository import Gtk
from gi.repository import Rsvg
from gi.repository import GdkPixbuf

from sugar3 import util
##import _camera


def get_string_from_pixbuf(pixbuf):
	data = [""]
	pixbuf.save_to_callbackv(_save_data_to_buffer_cb, "png", {}, data)
	return base64.b64encode(str(data[0]))


def _saveData_to_buffer_cb(buf, data):
	data[0] += buf
	return True


def get_pixbuf_from_string(str):
	pbl = GdkPixbuf.PixbufLoader()
	data = base64.b64decode(str)
	pbl.write(data)
	pbl.close()

	return pbl.get_pixbuf()


def load_svg(data, stroke, fill):
	if stroke == None or fill == None:
		return Rsvg.Handle.new_from_data(data)

	entity = '<!ENTITY fill_color "%s">' % fill
	data = re.sub('<!ENTITY fill_color .*>', entity, data)

	entity = '<!ENTITY stroke_color "%s">' % stroke
	data = re.sub('<!ENTITY stroke_color .*>', entity, data)

	return Rsvg.Handle.new_from_data(data)


def get_unique_filepath(path, i):
	path_ob = os.path.abspath(path)
	new_path = os.path.join(os.path.dirname(pathOb), str(str(i) + os.path.basename(pathOb)))
	if (os.path.exists(new_path)):
		i = i + 1
		return get_unique_filepath(path_ob, i)

	else:
		return os.path.abspath(new_path)


def md5_file(filepath):
	md = md5()
	f = file(filepath, 'rb')
	md.update(f.read())

	digest = md.hexdigest()
	hash = util.printable_hash(digest)
	return hash


def generate_thumbnail(pixbuf, scale, thumbw, thumbh):
	#need to generate thumbnail version here
	thumb_img = cairo.ImageSurface(cairo.FORMAT_ARGB32, thumbw, thumbh)
	tctx = cairo.Context(thumbImg)
	##img = _camera.cairo_surface_from_gdk_pixbuf(pixbuf)
	##tctx.scale(scale, scale)
	##tctx.set_source_surface(img, 0, 0)
	##tctx.paint()
	##gc.collect()
	return None ##thumbImg


def scale_svg_to_dim(handle, dim):
	#todo...
	scale = 1.0

	svg_dim = handle.get_dimension_data()
	if (svg_dim[0] > dim[0]):  # wtf?
		pass

	return scale


def get_date_string(when):
	#todo: internationalize the date
	return strftime("%a, %b %d, %I:%M:%S %p", time.localtime(when))


def gray_scale_pixbuf2(pb, copy):
	arr = pb.get_pixels_array()
	if (copy):
		arr = arr.copy()

	for row in arr:
		for pxl in row:
			y = 0.3*pxl[0][0]+0.59*pxl[1][0]+0.11*pxl[2][0]
			pxl[0][0] = y
			pxl[1][0] = y
			pxl[2][0] = y

	return GdkPixbuf.Pixbuf.new_from_data(arr, pb.get_colorspace(), pb.get_bits_per_sample())


def gray_scale_pixBuf(pb, copy):
	pb2 = GdkPixbuf.Pixbuf(GdkPixbuf.Colorspace.RGB, False, 8, pb.get_width(), pb.get_height())
	pb.saturate_and_pixelate(pb2, 0, 0)
	return pb2

