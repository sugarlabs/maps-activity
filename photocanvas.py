import cairo
import gtk
import gobject
from gtk import gdk

from p5 import P5
from constants import Constants

class PhotoCanvas(P5):

	def __init__(self):
		P5.__init__(self)
		self.img = None
		self.drawImg = None
		self.SCALING_IMG_ID = 0
		self.cacheWid = -1
		self.modify_bg( gtk.STATE_NORMAL, Constants.colorBlack.gColor )
		self.modify_bg( gtk.STATE_INSENSITIVE, Constants.colorBlack.gColor )


	def draw(self, ctx, w, h):
		self.fillRect( ctx, Constants.colorBlack, w, h )

		if (self.img != None):

			if (w == self.img.get_width()):
				self.cacheWid == w
				self.drawImg = self.img

			#only scale images when you need to, otherwise you're wasting cycles, fool!
			if (self.cacheWid != w):
				if (self.SCALING_IMG_ID == 0):
					self.drawImg = None
					self.SCALING_IMG_ID = gobject.idle_add( self.resizeImage, w, h )

			if (self.drawImg != None):
				#center the image based on the image size, and w & h
				ctx.set_source_surface(self.drawImg, (w/2)-(self.drawImg.get_width()/2), (h/2)-(self.drawImg.get_height()/2))
				ctx.paint()

			self.cacheWid = w


	def setImage(self, img):
		self.cacheWid = -1
		self.img = img
		self.drawImg = None
		self.queue_draw()


	def resizeImage(self, w, h):
		self.SCALING_IMG_ID = 0
		if (self.img == None):
			return

		#use image size in case 640 no more
		scaleImg = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
		sCtx = cairo.Context(scaleImg)
		sScl = (w+0.0)/(self.img.get_width()+0.0)
		sCtx.scale( sScl, sScl )
		sCtx.set_source_surface( self.img, 0, 0 )
		sCtx.paint()
		self.drawImg = scaleImg
		self.cacheWid = w
		self.queue_draw()
