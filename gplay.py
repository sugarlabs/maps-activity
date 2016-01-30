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

#look at jukeboxactivity.py

import gtk
import pygtk
pygtk.require('2.0')
import sys
import pygst
pygst.require('0.10')
import gst
import gst.interfaces
import gobject
import time
gobject.threads_init()

class Gplay:

	def __init__(self):
		self.window = None
		self.players = []
		self.playing = False
		self.nextMovie()

	def nextMovie(self):
		if ( len(self.players) > 0 ):
			self.playing = False
			self.getPlayer().set_property("video-sink", None)
			self.getPlayer().get_bus().disconnect(self.SYNC_ID)
			self.getPlayer().get_bus().remove_signal_watch()
			self.getPlayer().get_bus().disable_sync_message_emission()

		player = gst.element_factory_make("playbin", "playbin")
		xis = gst.element_factory_make("xvimagesink", "xvimagesink")
		player.set_property("video-sink", xis)
		bus = player.get_bus()
		bus.enable_sync_message_emission()
		bus.add_signal_watch()
		self.SYNC_ID = bus.connect('sync-message::element', self.onSyncMessage)
		self.players.append(player)


	def getPlayer(self):
		return self.players[len(self.players)-1]


	def onSyncMessage(self, bus, message):
		if message.structure is None:
			return True
		if message.structure.get_name() == 'prepare-xwindow-id':
			self.window.set_sink(message.src)
			message.src.set_property('force-aspect-ratio', True)
			return True


	def setLocation(self, location):
		print("setLocation: ", location )
		if (self.getPlayer().get_property('uri') == location):
			self.seek(gst.SECOND*0)
			return

		self.getPlayer().set_state(gst.STATE_READY)
		self.getPlayer().set_property('uri', location)
		ext = location[len(location)-3:]
		if (ext == "jpg"):
			self.pause()
		print("all played?")


	def queryPosition(self):
		"Returns a (position, duration) tuple"
		try:
			position, format = self.getPlayer().query_position(gst.FORMAT_TIME)
		except:
			position = gst.CLOCK_TIME_NONE

		try:
			duration, format = self.getPlayer().query_duration(gst.FORMAT_TIME)
		except:
			duration = gst.CLOCK_TIME_NONE

		return (position, duration)


	def seek(self, location):
		event = gst.event_new_seek(1.0, gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_ACCURATE, gst.SEEK_TYPE_SET, location, gst.SEEK_TYPE_NONE, 0)
		res = self.getPlayer().send_event(event)
		if res:
			self.getPlayer().set_new_stream_time(0L)


	def pause(self):
		self.playing = False
		self.getPlayer().set_state(gst.STATE_PAUSED)


	def play(self):
		self.playing = True
		self.getPlayer().set_state(gst.STATE_PLAYING)


	def stop(self):
		self.playing = False
		self.getPlayer().set_state(gst.STATE_NULL)
		self.nextMovie()


	def get_state(self, timeout=1):
		return self.getPlayer().get_state(timeout=timeout)


	def is_playing(self):
		return self.playing



class PlayVideoWindow(gtk.EventBox):
	def __init__(self, bgd):
		gtk.EventBox.__init__(self)

		self.imagesink = None

		self.modify_bg( gtk.STATE_NORMAL, bgd )
		self.modify_bg( gtk.STATE_INSENSITIVE, bgd )
		self.unset_flags(gtk.DOUBLE_BUFFERED)
		self.set_flags(gtk.APP_PAINTABLE)


	def set_sink(self, sink):
		if (self.imagesink != None):
			assert self.window.xid
			self.imagesink = None
			del self.imagesink

		self.imagesink = sink
		self.imagesink.set_xwindow_id(self.window.xid)