# Copyright (C) 2007, One Laptop Per Child
# Copyright (c) 2008, Media Modifications Ltd.
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

import gtk

from sugar.graphics.objectchooser import ObjectChooser

class FilePicker:

	def __init__(self):
		pass


	def show(self):
		title = None
		parent = None
		file = None
		job = None
		chooser = ObjectChooser()

		try:
			result = chooser.run()
			if result == gtk.RESPONSE_ACCEPT:
				jobject = chooser.get_selected_object()
				if (jobject and jobject.file_path):
					job = jobject

		finally:
			chooser.destroy()
			del chooser

		return job
