import gtk
import os
import gobject
import rsvg
import gc

from sugar.graphics.palette import Palette
from sugar.graphics.tray import TrayButton
from sugar.graphics.icon import Icon
from sugar.graphics import style
from constants import Constants
import utils

class SavedButton(TrayButton, gobject.GObject):
	def __init__(self, ui, savedmapData):
		TrayButton.__init__(self)
		self.ui = ui
		self.data = savedmapData

		img = self.getImg()
		self.set_icon_widget( img )

		self.setup_rollover_options()


	def getImg( self ):
		pb = gtk.gdk.pixbuf_new_from_file(self.data.thumbPath)

		img = gtk.Image()
		img.set_from_pixbuf(pb)
		img.show()

		return img


	def setButtClickedId( self, id ):
		self.BUTT_CLICKED_ID = id


	def getButtClickedId( self ):
		return self.BUTT_CLICKED_ID


	def setup_rollover_options( self ):
		palette = Palette( Constants.istrSavedMap )
		self.set_palette(palette)

		self.tag_menu_item = gtk.MenuItem( Constants.istrTagMap  )
		self.ACTIVATE_TAG_ID = self.tag_menu_item.connect('activate', self._tagCb)
		palette.menu.append(self.tag_menu_item)
		self.tag_menu_item.show()

		self.rem_menu_item = gtk.MenuItem( Constants.istrRemove  )
		self.ACTIVATE_REMOVE_ID = self.rem_menu_item.connect('activate', self._itemRemoveCb)
		palette.menu.append(self.rem_menu_item)
		self.rem_menu_item.show()

		self.copy_menu_item = gtk.MenuItem( Constants.istrCopyToClipboard )
		self.ACTIVATE_COPY_ID = self.copy_menu_item.connect('activate', self._itemCopyToClipboardCb)
		self.get_palette().menu.append(self.copy_menu_item)
		self.copy_menu_item.show()


	def cleanUp( self ):
		self.rem_menu_item.disconnect( self.ACTIVATE_REMOVE_ID )
		self.copy_menu_item.disconnect( self.ACTIVATE_COPY_ID )
		self.tag_menu_item.disconnect( self.ACTIVATE_TAG_ID)


	def _tagCb(self, widget):
		self.ui.showSearchResultTags( self.data )


	def _itemRemoveCb(self, widget):
		self.ui.removeThumb( self.data )


	def _itemCopyToClipboardCb(self, widget):
		self.ui.copyToClipboard( self.data )
