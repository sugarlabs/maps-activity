import os
import gtk
from gettext import gettext as _

import sugar.graphics.style
from sugar.activity import activity
from sugar import profile

from instance import Instance
from color import Color
import utils

class Constants:

	VERSION = 8

	SERVICE = "org.laptop.Map"
	IFACE = SERVICE
	PATH = "/org/laptop/Map"
	activityId = None

	gfxPath = os.path.join(activity.get_bundle_path(), "gfx")
	htmlPath = os.path.join(activity.get_bundle_path(), "html")
	iconsPath = os.path.join(activity.get_bundle_path(), "icons")

	istrAnnotate = _("Edit")
	istrSearch = _("Search")
	istrSearchAddress = _('Find:')
	istrSearchMedia = _("Tags:")
	istrSaveSearch = _("Save Search")
	istrConnecting = _("Connecting to Map Server")
	istrZoomIn = _("Zoom In")
	istrZoomOut = _("Zoom Out")
	istrSaveSearch = _("Save")
	istrDensity = _("Density")
	istrSavedMap = _("Saved Map")
	istrTagMap = _("Describe Map")
	istrRemove = _("Remove Map")
	istrCopyToClipboard = _("Copy to Clipboard")
	istrAddMedia = _("Add Media")
	istrAddInfo = _("Add Info")
	istrDeleteMedia = _("Delete")
	istrWebMedia = _("Library")
	istrMeasure = _("Measure")
	istrStaticMaps = _("olpcMAP.net")
	istrPanoramio = _("Panoramio")
	istrLocalWiki = _("LocationWiki")
	istrWikiMapia = _("WikiMapia")
	istrLatitude = _("Latitude:")
	istrLongitude = _("Longitude:")
	istrTags = _("Description:")
	istrLang = _("lang=en")
	LineButton = _("Add Line")
	PolyButton = _("Add Shape")

	TYPE_PHOTO = 0
	TYPE_VIDEO = 1

	ui_dim_INSET = 4

	recdAlbum = "map"
	recdLat = "lat"
	recdLng = "lng"
	recdDatastoreId = "datastore"
	recdInfo = "info"
	recdMapItem = "mapItem"
	recdSavedMapItem = "savedMap"
	recdInfoMarker = "infoMarker"
	recdIcon = "icon"
	recdZoom = "zoom"
	recdNotes = "notes"
	recdMapImg = "mapImg"
	recdTags = "tags"
	recdMapThumbImg = "mapThumbImg"
	recdRecdId = "recdId"
	recdRecdLat = "recdLat"
	recdRecdLng = "recdLng"
	recdDensity = "density"
	recdLine = "line"
	lineID = "lid"
	lineColor = "lcolor"
	lineThick = "lthickness"
	linePts = "lpts"
	mapLat="lat"
	mapLng="lng"
	mapZoom="zoom"

	colorBlack = Color()
	colorBlack.init_rgba( 0, 0, 0, 255 )
	colorWhite = Color()
	colorWhite.init_rgba( 255, 255, 255, 255 )
	colorRed = Color()
	colorRed.init_rgba( 255, 0, 0, 255)
	colorGreen = Color()
	colorGreen.init_rgba( 0, 255, 0, 255)
	colorBlue = Color()
	colorBlue.init_rgba( 0, 0, 255, 255)
	colorGrey = Color()
	colorGrey.init_gdk( sugar.graphics.style.COLOR_BUTTON_GREY )
	colorBg = colorBlack

	def __init__( self, ca ):
		self.__class__.activityId = ca._activity_id
		self.__class__.northImgClr, self.__class__.northImgBw = self.loadSvgImg('map-icon-croseN.svg')
		self.__class__.southImgClr, self.__class__.southImgBw = self.loadSvgImg('map-icon-croseS.svg')
		self.__class__.eastImgClr, self.__class__.eastImgBw = self.loadSvgImg('map-icon-croseE.svg')
		self.__class__.westImgClr, self.__class__.westImgBw = self.loadSvgImg('map-icon-croseW.svg')

		infoOnSvgPath = os.path.join(self.__class__.iconsPath, 'corner-info.svg')
		infoOnSvgFile = open(infoOnSvgPath, 'r')
		infoOnSvgData = infoOnSvgFile.read()
		self.__class__.infoOnSvg = utils.loadSvg(infoOnSvgData, None, None )
		infoOnSvgFile.close()

	def loadSvgImg(self, fileName):
		SvgPath = os.path.join(self.__class__.iconsPath, fileName)
		SvgFile = open(SvgPath, 'r')
		SvgData = SvgFile.read()
		SvgFile.close()

		ColorSvg = utils.loadSvg(SvgData, Instance.colorStroke.hex, Instance.colorFill.hex)
		ColorPixBuf = ColorSvg.get_pixbuf()
		ColorImg = gtk.Image()
		ColorImg.set_from_pixbuf(ColorPixBuf)

		MonoSvg = utils.loadSvg(SvgData, self.__class__.colorGrey.hex, self.__class__.colorWhite.hex)
		MonoPixBuf = MonoSvg.get_pixbuf()
		MonoImg = gtk.Image()
		MonoImg.set_from_pixbuf(MonoPixBuf)

		return [ColorImg, MonoImg]
