#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2008, Media Modifications Ltd.
# Copyright (c) 2016, Cristian García.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
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

# look at jukeboxactivity.py
import gi
from gi.repository import Gtk
gi.require_version('Gst', '1.0')
from gi.repository import Gst
from gi.repository import GLib

GLib.threads_init()
Gst.init([])


class Gplay:

    def __init__(self):
        self.window = None
        self.players = []
        self.playing = False
        self.next_movie()

    def next_movie(self):
        if len(self.players) > 0:
            self.playing = False
            self.get_player().set_property("video-sink", None)
            self.get_player().get_bus().disconnect(self.SYNC_ID)
            self.get_player().get_bus().remove_signal_watch()
            self.get_player().get_bus().disable_sync_message_emission()

        player = Gst.ElementFactory.make("playbin", "playbin")
        xis = Gst.ElementFactory.make("xvimagesink", "xvimagesink")
        player.set_property("video-sink", xis)
        bus = player.get_bus()
        bus.enable_sync_message_emission()
        bus.add_signal_watch()
        self.SYNC_ID = bus.connect(
            'sync-message::element',
            self.on_sync_message)
        self.players.append(player)

    def get_player(self):
        return self.players[len(self.players) - 1]

    def on_sync_message(self, bus, message):
        if message.get_structure is None:
            return True

        if message.get_structure.get_name() == 'prepare-xwindow-id':
            self.window.set_sink(message.src)
            message.src.set_property('force-aspect-ratio', True)
            return True

    def set_location(self, location):
        print("set_location: ", location)
        if (self.getPlayer().get_property('uri') == location):
            self.seek(Gst.SECOND * 0)
            return

        self.get_player().set_state(Gst.State.READY)
        self.get_player().set_property('uri', location)

        ext = location[len(location) - 3:]
        if (ext == "jpg"):
            self.pause()

        print("all played?")

    def query_position(self):
        "Returns a (position, duration) tuple"
        try:
            position, format = self.get_player().query_position(Gst.Format.TIME)
        except BaseException:
            position = Gst.CLOCK_TIME_NONE

        try:
            duration, format = self.getPlayer().query_duration(Gst.Format.TIME)
        except BaseException:
            duration = Gst.CLOCK_TIME_NONE

        return (position, duration)

    def seek(self, location):
        event = Gst.Event.new_seek(
            1.0,
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
            Gst.SeekType.SET,
            location,
            Gst.SeekType.NONE,
            0)
        res = self.get_player().send_event(event)
        if res:
            self.get_player().set_new_stream_time(0)

    def pause(self):
        self.playing = False
        self.get_player().set_state(Gst.State.PAUSED)

    def play(self):
        self.playing = True
        self.get_player().set_state(Gst.State.PLAYING)

    def stop(self):
        self.playing = False
        self.get_player().set_state(Gst.State.NULL)
        self.next_movie()

    def get_state(self, timeout=1):
        return self.get_player().get_state(timeout=timeout)

    def is_playing(self):
        return self.playing


class PlayVideoWindow(Gtk.EventBox):

    def __init__(self, bgd):
        Gtk.EventBox.__init__(self)

        self.imagesink = None

        self.modify_bg(Gtk.StateType.NORMAL, bgd)
        self.modify_bg(Gtk.StateType.INSENSITIVE, bgd)
        self.set_double_buffered(False)
        self.set_app_paintable(True)

    def set_sink(self, sink):
        if self.imagesink is not None:
            assert self.get_window().xid
            self.imagesink = None
            del self.imagesink

        self.imagesink = sink
        self.imagesink.set_xwindow_id(self.window.xid)
