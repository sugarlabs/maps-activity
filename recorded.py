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

import os
import map
import gtk

from constants import Constants
from instance import Instance

class Recorded:
	SOURCE_DATASTORE = 0
	SOURCE_LOCAL = 1
	SOURCE_BUNDLE = 2

	def __init__(self):
		self.name = None
		self.recorded = None
		self.colorStroke = None
		self.colorFill = None
		self.type = None

		self.latitude = None
		self.longitude = None

		self.thumbFilename = None
		self.fileName = None
		self.datastoreOb = None
		self.datastoreId = None
		self.tags = ""

		self.source = 0


	def getFilepath(self):
		if (self.source == self.__class__.SOURCE_BUNDLE):
			path = os.path.join( Constants.htmlPath, self.fileName )
			return path
		elif (self.source == self.__class__.SOURCE_DATASTORE):
			return self.datastoreOb.file_path
		else:
			return None


	def getPixBuf(self):
		pb = None

		fp = self.getFilepath()
		if (fp != None):
			pb = gtk.gdk.pixbuf_new_from_file(fp)

		return pb


	def getThumbUrl(self):
		return "http://127.0.0.1:" + str(map.Map.ajaxPort) + "/getImage.js?id="


	def getThumbBasename(self):
		return str(self.thumbFilename)


	def getThumbPath(self):
		thumbPath = os.path.join( Instance.instancePath, self.getThumbBasename() )
		return thumbPath