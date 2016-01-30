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

from constants import Constants
from recorded import Recorded
from color import Color
from instance import Instance
import utils
from recorded import Recorded

import gtk
import os
import shutil
import StringIO

class Model:
	def __init__(self, ca):
		self.ca = ca

		self.recs = []
		self.savedMaps = []
		self.infoMarkers = {}
		self.lineData = {}

	def getMediaByThumbFilename(self, id):
		for i in range(len(self.recs)):
			if (self.recs[i].thumbFilename == id):
				return self.recs[i]

		return None


	def getMediaByDatastoreId(self, id):
		for i in range(len(self.recs)):
			if (self.recs[i].datastoreId == id):
				return self.recs[i]

		return None


	def addMedia(self, lat, lon, datastoreOb):
		rec = Recorded()

		#default photo
		rec.type = Constants.TYPE_PHOTO
		if((datastoreOb.metadata['mime_type'] == "video/ogg") or (datastoreOb.metadata['mime_type'] == "audio/ogg")):
			rec.type = Constants.TYPE_VIDEO

		rec.source = Recorded.SOURCE_DATASTORE
		rec.datastoreOb = datastoreOb
		rec.datastoreId = datastoreOb.object_id

		rec.tags = ""
		if (datastoreOb.metadata.has_key("tags")):
			rec.tags = datastoreOb.metadata['tags']

		rec.latitude = lat
		rec.longitude = lon
		

		colors = datastoreOb.metadata['icon-color']
		colorStroke, colorFill = colors.split(",")
		rec.colorStroke = Color()
		rec.colorStroke.init_hex(colorStroke)
		rec.colorFill = Color()
		rec.colorFill.init_hex(colorFill)

		thumbPixbuf = None
		if (datastoreOb.metadata.has_key("preview")):
			try:
				thumb = datastoreOb.metadata['preview']
				if thumb[1:4] == 'PNG':
					pbl = gtk.gdk.PixbufLoader()
					pbl.write(thumb)
					pbl.close()
					thumbPixbuf = pbl.get_pixbuf()
				else:
					thumbPixbuf = utils.getPixbufFromString(thumb)
			except:
				pass

		if (thumbPixbuf == None):
			#try to create the thumbnail yourself...
			if (rec.type == Constants.TYPE_PHOTO):
				try:
					#load in the image, make a thumbnail
					thumbPixbuf = gtk.gdk.pixbuf_new_from_file_at_size(rec.getFilepath(), 320, 240)
				except:
					pass

		if (thumbPixbuf == None):
			#i give up.  load in a blank image from the activity itself.
			thumbPath = os.path.join(self.ca.htmlPath, "1.jpg")
			thumbPixbuf = gtk.gdk.pixbuf_new_from_file(thumbPath)


		thumbFilepath = os.path.join(Instance.instancePath, "thumb.png")
		thumbFilepath = utils.getUniqueFilepath(thumbFilepath, 0)
		thumbPixbuf.save( thumbFilepath, "png", {} )
		rec.thumbFilename = os.path.basename(thumbFilepath)

		self.recs.append(rec)

		return rec

	def setInfo( self, lat, lng, info, icon ):
		self.infoMarkers[lat+','+lng] = lat + ";~" + lng + ";~" + info + ";~" + icon

	def setLine( self, id, color, thickness, pts ):
		self.lineData[id] = id + ";~" + color + ";~" + thickness + ";~" + pts

	def addSavedMap( self, smap ):
		self.savedMaps.append(smap)

	def getMediaResponse(self, s, w, n, e):
		r = ""

		for i in range( len(self.recs) ):
			rec = self.recs[i]
			r = r + "var m" + str(i) + " = new MediaMarker( new google.maps.LatLng(" + str(rec.latitude) + "," + str(rec.longitude) + "), '" + rec.getThumbUrl() + "', '" + rec.getThumbBasename() + "', null, null, 'null');"
			r = r + "canvas.markerList.addMarker(m" + str(i) + ");"

		for k, i in self.infoMarkers.iteritems():
			iMarker = i.split(";~")
			r = r + "addInfoMarker(" + iMarker[0] + "," + iMarker[1] + ",'" + iMarker[2] + "','" + iMarker[3] + "');"

		for k, i in self.lineData.iteritems():
			iLine = i.split(";~")
			r = r + "addLine('" + iLine[0] + "','" + iLine[1] + "','" + iLine[2] + "','" + iLine[3] + "');"
		return r
