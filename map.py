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

import os
import threading
from threading import *
import time
import shutil
import urllib
import random
import gi

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import GdkPixbuf

from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.graphics.toolbarbox import ToolbarButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity import activity

from filepicker import FilePicker

from constants import Constants
from webviewer import WebViewer
from server import Server
from logic import ServerLogic
from instance import Instance
from model import Model
from tray import HTray
from photocanvas import PhotoCanvas
from p5 import P5
from gplay import Gplay
from gplay import PlayVideoWindow
import serialize
import utils
from button import SavedButton
from savedmap import SavedMap

# sharing
import telepathy
from dbus.service import method, signal
from dbus.gobject_service import ExportedGObject
from sugar3.presence import presenceservice
from sugar3.presence.tubeconn import TubeConnection

SERVICE = "org.laptop.map"
IFACE = SERVICE
PATH = "/org/laptop/map"

img_width = 180
img_height = 135
web_width = img_width * 4
webHeight = img_height * 3


class Map(activity.Activity):

    # temp values until they get assigned
    cometPort = 8889
    ajaxPort = 8890

    initLat = '48.224'
    initLng = '-11.07'
    initZoom = '3'
    initType = 'terr'

    popW = 320
    popH = 240
    popB = 10

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        Instance(self)
        Constants(self)
        self.modify_bg(Gtk.StateType.NORMAL, Constants.color_bg.g_color)

        GLib.idle_add(self._initme, None)

    def _initme(self, userdata=None):
        self.basePath = activity.get_bundle_path()
        self.htmlPath = os.path.join(self.basePath, "html")
        self.libPath = "/home/olpc/Library/MapPack/"  # If the user isn't olpc?
        self.m = Model(self)
        self.cond = Condition()

        self.SAVING_SEARCH = False
        self.shownSave = None
        self.shownRecd = None
        # these get updated whenever we hear back from the server
        self.NOW_MAP_CENTER_LAT = self.__class__.initLat
        self.NOW_MAP_CENTER_LNG = self.__class__.initLng
        self.NOW_MAP_ZOOM = self.__class__.initZoom
        self.NOW_MAP_TAGS = ""

        # calc unique ports
        h = hash(Instance.instance_id)
        self.__class__.cometPort = 1024 + (h % 32255) * 2
        self.__class__.ajaxPort = self.__class__.cometPort + 1

        # ui
        self.windowStack = []

        self.toolbarbox = ToolbarBox()
        self.set_toolbar_box(self.toolbarbox)

        self.toolbarbox.toolbar.insert(ActivityToolbarButton(self), -1)
        self.toolbarbox.toolbar.insert(Gtk.SeparatorToolItem(), -1)
        self.toolbarbox.toolbar.insert(StopButton(self), -1)

        sep = Gtk.SeparatorToolItem()
        sep.props.draw = False
        sep.set_expand(True)
        self.toolbarbox.toolbar.insert(sep, 2)

        self.searchToolbar = SearchToolbar(self)
        self.searchToolbar.connect("address-update", self._addressUpdateCb)
        self.searchToolbar.connect("zoom-in", self._zoomInCb)
        self.searchToolbar.connect("zoom-out", self._zoomOutCb)
        self.searchToolbar.connect("save-search", self._saveSearchCb)
        self.searchToolbar.connect("search-update", self._searchUpdateCb)
        self.searchToolbar.set_sensitive(False)
        self.toolbarbox.toolbar.insert(
            ToolbarButton(
                page=self.searchToolbar,
                icon_name='edit-find'),
            2)
        self.addToolbar = AddToolbar(self)
        self.toolbarbox.toolbar.insert(
            ToolbarButton(
                page=self.addToolbar,
                icon_name='list-add'),
            3)
        self.addToolbar.connect("add-media", self._addMediaCb)
        self.addToolbar.connect("add-kml", self._addKMLCb)
        self.addToolbar.connect("add-info", self._addInfoCb)
        self.addToolbar.connect("delete-media", self._deleteMediaCb)
        self.addToolbar.connect("measure", self._measureCb)
        self.addToolbar.connect("olpcmap", self._olpcmapCb)
        self.addToolbar.connect("panoramio", self._panoramioCb)
        self.addToolbar.connect("local-wiki", self._localwikiCb)
        self.addToolbar.connect("wikimapia", self._wikimapiaCb)
        self.addToolbar.set_sensitive(False)
        self.firstSearch = True
        self.addToolbar.show_all()
        # add components
        vbox = Gtk.VBox()

        vboxNorth = Gtk.VBox()
        vbox.pack_start(vboxNorth, True, True, 0)
        buttNorthFiller = Gtk.EventBox()
        buttNorthFiller.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_bg.g_color)
        buttNorthFiller.modify_bg(
            Gtk.StateType.ACTIVE,
            Constants.color_bg.g_color)
        buttNorthFiller.modify_bg(
            Gtk.StateType.INSENSITIVE,
            Constants.color_bg.g_color)
        vboxNorth.pack_start(buttNorthFiller, True, True, 0)
        buttNorthEventBox = Gtk.EventBox()
        buttNorthEventBox.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_bg.g_color)
        buttNorthEventBox.modify_bg(
            Gtk.StateType.ACTIVE,
            Constants.color_bg.g_color)
        buttNorthEventBox.modify_bg(
            Gtk.StateType.INSENSITIVE,
            Constants.color_bg.g_color)
        self.buttNorth = Gtk.Button()
        self.buttNorth.set_property("can-focus", False)
        self.buttNorth.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_bg.g_color)
        self.buttNorth.modify_bg(
            Gtk.StateType.ACTIVE,
            Constants.color_bg.g_color)
        self.buttNorth.modify_bg(
            Gtk.StateType.INSENSITIVE,
            Constants.color_bg.g_color)
        buttNorthEventBox.add(self.buttNorth)
        # self.buttNorth.set_image(Constants.north_img_clr)
        self.buttNorth.connect('clicked', self._buttNorthCb)
        vboxNorth.pack_start(buttNorthEventBox, False, False, 0)
        self.buttNorth.set_relief(Gtk.ReliefStyle.NONE)

        hbox = Gtk.HBox()
        self.htmlScale = 1.43
        hbox.set_size_request(-1, int(webHeight * self.htmlScale))
        vbox.pack_start(hbox, False, False, 0)

        vboxSouth = Gtk.VBox()
        vbox.pack_start(vboxSouth, True, True, 0)
        buttSouthEventBox = Gtk.EventBox()
        buttSouthEventBox.modify_bg(
            Gtk.StateType.ACTIVE,
            Constants.color_bg.g_color)
        buttSouthEventBox.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_bg.g_color)
        buttSouthEventBox.modify_bg(
            Gtk.StateType.INSENSITIVE,
            Constants.color_bg.g_color)
        vboxSouth.pack_start(buttSouthEventBox, False, False, 0)
        self.buttSouth = Gtk.Button()
        self.buttSouth.set_property("can-focus", False)
        self.buttSouth.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_bg.g_color)
        self.buttSouth.modify_bg(
            Gtk.StateType.ACTIVE,
            Constants.color_bg.g_color)
        self.buttSouth.modify_bg(
            Gtk.StateType.INSENSITIVE,
            Constants.color_bg.g_color)
        buttSouthEventBox.add(self.buttSouth)
        # self.buttSouth.set_image(Constants.south_img_clr)
        self.buttSouth.connect('clicked', self._buttSouthCb)
        buttSouthFiller = Gtk.EventBox()
        buttSouthFiller.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_bg.g_color)
        buttSouthFiller.modify_bg(
            Gtk.StateType.ACTIVE,
            Constants.color_bg.g_color)
        buttSouthFiller.modify_bg(
            Gtk.StateType.INSENSITIVE,
            Constants.color_bg.g_color)
        vboxSouth.pack_start(buttSouthFiller, True, True, 0)
        self.buttSouth.set_relief(Gtk.ReliefStyle.NONE)

        self.tray = HTray()
        self.tray.set_size_request(-1, 130)
        self.tray.connect("enter-notify-event", self._trayMouseCb)
        self.tray.viewport.connect("enter-notify-event", self._trayMouseCb)
        self.tray.viewport.traybar.connect(
            "enter-notify-event", self._trayMouseCb)
        self.tray.scroll_left.connect("enter-notify-event", self._trayMouseCb)
        self.tray.scroll_right.connect("enter-notify-event", self._trayMouseCb)
        self.tray.scroll_left_event.connect(
            "enter-notify-event", self._trayMouseCb)
        self.tray.scroll_right_event.connect(
            "enter-notify-event", self._trayMouseCb)
        fakeTray = Gtk.VBox()
        fakeTray.set_size_request(-1, 130)
        fakeTray.modify_bg(Gtk.StateType.NORMAL, Constants.color_bg.g_color)
        fakeTrayEvent = Gtk.EventBox()
        fakeTrayEvent.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_bg.g_color)
        fakeTrayEvent.set_size_request(-1, 130)
        fakeTrayEvent.add(fakeTray)
        self.trayBox = Gtk.Notebook()
        self.trayBox.set_size_request(-1, 130)
        self.trayBox.set_show_tabs(False)
        vbox.pack_start(self.trayBox, False, False, 0)
        self.trayBox.append_page(self.tray, Gtk.Label(""))
        self.trayBox.append_page(fakeTrayEvent, Gtk.Label(""))
        self.realTrayIndex = self.trayBox.page_num(self.tray)
        self.fakeTrayIndex = self.trayBox.page_num(fakeTrayEvent)
        self.trayBox.set_current_page(self.realTrayIndex)
        fakeTrayEvent.add_events(Gdk.EventMask.VISIBILITY_NOTIFY_MASK)
        fakeTrayEvent.connect_after(
            "visibility-notify-event",
            self._fakeTrayVisibleNotifyCb)

        hboxWest = Gtk.HBox()
        hbox.pack_start(hboxWest, True, True, 0)
        buttWestFiller = Gtk.EventBox()
        buttWestFiller.modify_bg(
            Gtk.StateType.ACTIVE,
            Constants.color_bg.g_color)
        buttWestFiller.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_bg.g_color)
        buttWestFiller.modify_bg(
            Gtk.StateType.INSENSITIVE,
            Constants.color_bg.g_color)
        hboxWest.pack_start(buttWestFiller, True, True, 0)
        buttWestEventBox = Gtk.EventBox()
        hboxWest.pack_start(buttWestEventBox, True, True, 0)
        buttWestEventBox.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_bg.g_color)
        buttWestEventBox.modify_bg(
            Gtk.StateType.ACTIVE,
            Constants.color_bg.g_color)
        buttWestEventBox.modify_bg(
            Gtk.StateType.INSENSITIVE,
            Constants.color_bg.g_color)
        self.buttWest = Gtk.Button()
        self.buttWest.set_property("can-focus", False)
        buttWestEventBox.add(self.buttWest)
        self.buttWest.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_bg.g_color)
        self.buttWest.modify_bg(
            Gtk.StateType.ACTIVE,
            Constants.color_bg.g_color)
        self.buttWest.modify_bg(
            Gtk.StateType.INSENSITIVE,
            Constants.color_bg.g_color)
        # self.buttWest.set_image(Constants.west_img_clr)
        self.buttWest.connect('clicked', self._buttWestCb)
        self.buttWest.set_relief(Gtk.ReliefStyle.NONE)

        self.browseBox = Gtk.VBox()
        self.browser = WebViewer()
        self.browser.set_size_request(
            int(web_width * self.htmlScale), int(webHeight * self.htmlScale))
        self.browseBox.pack_start(self.browser, True, True, 0)
        self.browseBox.set_size_request(
            int(web_width * self.htmlScale), int(webHeight * self.htmlScale))
        hbox.pack_start(self.browseBox, True, True, 0)

        hboxEast = Gtk.HBox()
        hbox.pack_start(hboxEast, True, True, 0)
        buttEastEventBox = Gtk.EventBox()
        hboxEast.pack_start(buttEastEventBox, True, True, 0)
        buttEastEventBox.modify_bg(
            Gtk.StateType.ACTIVE,
            Constants.color_bg.g_color)
        buttEastEventBox.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_bg.g_color)
        buttEastEventBox.modify_bg(
            Gtk.StateType.INSENSITIVE,
            Constants.color_bg.g_color)
        self.buttEast = Gtk.Button()
        self.buttEast.set_property("can-focus", False)
        self.buttEast.modify_bg(
            Gtk.StateType.ACTIVE,
            Constants.color_bg.g_color)
        self.buttEast.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_bg.g_color)
        self.buttEast.modify_bg(
            Gtk.StateType.INSENSITIVE,
            Constants.color_bg.g_color)
        buttEastEventBox.add(self.buttEast)
        # self.buttEast.set_image(Constants.east_img)
        buttEastFiller = Gtk.EventBox()
        hboxEast.pack_start(buttEastFiller, True, True, 0)
        buttEastFiller.modify_bg(
            Gtk.StateType.ACTIVE,
            Constants.color_bg.g_color)
        buttEastFiller.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_bg.g_color)
        buttEastFiller.modify_bg(
            Gtk.StateType.INSENSITIVE,
            Constants.color_bg.g_color)
        self.buttEast.connect('clicked', self._buttEastCb)
        self.buttEast.set_relief(Gtk.ReliefStyle.NONE)

        # important to call these in this order to ensure they show up
        self.set_canvas(vbox)
        self.browser.show()

        # fire up the web engine, spiderman!
        self.cometLogic = ServerLogic(self)

        self.ajaxServer = ServerThread(
            self.__class__.ajaxPort, self.cometLogic)
        self.ajaxServer.start()

        self.cometServer = ServerThread(
            self.__class__.cometPort, self.cometLogic)
        self.cometServer.start()

        self.browser.load_uri("file://" +
                              self.htmlPath +
                              "/staticmap2.html?ajaxPort=" +
                              str(self.__class__.ajaxPort) +
                              "&cometPort=" +
                              str(self.__class__.cometPort) +
                              "&xo=true" +
                              "&lat=" +
                              str(self.NOW_MAP_CENTER_LAT) +
                              "&lng=" +
                              str(self.NOW_MAP_CENTER_LNG) +
                              "&zoom=" +
                              str(self.NOW_MAP_ZOOM) +
                              "&type=" +
                              self.__class__.initType +
                              "&" +
                              Constants.istr_lang)

        self.loaded = True
        self.loadingWindow = Gtk.Window()
        self.addToWindowStack(self.loadingWindow, self)
        self.loadingWindow.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_black.g_color)
        loadingVBox = Gtk.VBox()
        self.loadingWindow.add(loadingVBox)

        loadingTopEventBox = Gtk.EventBox()
        loadingTopEventBox.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_black.g_color)
        loadingVBox.pack_start(loadingTopEventBox, True, True, 0)

        self.loadingCanvas = PhotoCanvas()
        self.loadingCanvas.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_black.g_color)
        self.loadingCanvas.set_size_request(1200, 600)
        loadingVBox.pack_start(self.loadingCanvas, True, True, 0)

        loadingInfo = Gtk.Label()
        loadingInfo.set_alignment(.5, 0)
        loadingInfo.set_markup(
            "<b><span foreground='white' size='xx-large'>" +
            Constants.istr_connecting +
            "</span></b>")
        loadingVBox.pack_start(loadingInfo, False, False, 0)

        loadingBotEventBox = Gtk.EventBox()
        loadingBotEventBox.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_black.g_color)
        loadingVBox.pack_start(loadingBotEventBox, True, True, 0)
        self.loadingWindow.resize(
            Gdk.Screen.width(),
            Gdk.Screen.height() -
            self.toolbarbox.get_allocation().height)
        self.moveWinOffscreen(self.loadingWindow)

        self.popWindow = Gtk.Window()
        self.addToWindowStack(self.popWindow, self.loadingWindow)
        self.popWindow.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_black.g_color)
        self.popWindow.resize(self.popW + (2 * self.popB),
                              self.popH + (2 * self.popB))
        self.popUpBg = PopUpP5()
        self.popWindow.add(self.popUpBg)
        self.moveWinOffscreen(self.popWindow)
        self.popWindow.show_all()

        self.mediaWindow = Gtk.Window()
        self.addToWindowStack(self.mediaWindow, self.popWindow)
        self.moveWinOffscreen(self.mediaWindow)
        self.mediaWindow.show_all()

        self.infoWindow = Gtk.Window()
        self._fillInInfoWindow()
        self.addToWindowStack(self.infoWindow, self.mediaWindow)
        self.moveWinOffscreen(self.infoWindow)
        self.infoWindow.show_all()

        self.selectWindow = Gtk.Window()
        self.selectWindow.modify_bg(
            Gtk.StateType.NORMAL,
            Constants.color_black.g_color)
        self.addToWindowStack(self.selectWindow, self.infoWindow)
        self.moveWinOffscreen(self.selectWindow)
        self.selectWindow.show_all()

        self.photoCanvas = PhotoCanvas()

        self.gplayWin = PlayVideoWindow(Constants.color_black.g_color)
        self.gplay = Gplay()
        self.gplay.window = self.gplayWin

        self.connect("destroy", self.destroy)
        self.toolbarbox_SIZE_ALLOCATE_ID = self.toolbarbox.connect_after(
            "size-allocate", self._sizeAllocateCb)
        self.show_all()

        # break loading screen
        self.loaded = True
        self.enableNavigation()

        # add sharing
        self.maptube = None  # Shared session
        self.initiating = False
        self.pservice = presenceservice.get_instance()
        owner = self.pservice.get_owner()
        self.owner = owner
        self.connect('shared', self._shared_cb)
        self.connect('joined', self._joined_cb)
        self.mediaType = "photo"

        return False

    def _received_cb(self, text):
        if(text.find(",") != -1):
            params = text.split(",")
            if(params[0] == "loc"):
                # other XO's map location has moved [lat,lng,zoom]
                self.preComet()
                self.cometLogic.handleReceivedMap(
                    params[1], params[2], params[3])
                self.postComet()
            elif(params[0] == "mar"):
                # other XO has added or modded info marker
                # [lat,lng,infoText,iconImg]
                if(self.cometLogic.addKMLSet == 0):
                    self.preComet()
                self.cometLogic.handleAddMarker(
                    params[1], params[2], params[3], params[4])
                self.m.setInfo(params[1], params[2], params[3], params[4])
                # self.cometLogic.handleEndKML()
                if(self.cometLogic.addKMLSet == 0):
                    self.postComet()
            elif(params[0] == "del"):
                # delete a marker (not working)
                self.preComet()
                self.cometLogic.handleDelete()
                self.postComet()
            elif(params[0] == "smap"):
                # add SavedMap [lat,lng,zoom,info] + not-new reminder
                self.addSavedMap(
                    params[1],
                    params[2],
                    params[3],
                    params[4],
                    False)
            elif(params[0] == "line"):
                # add a line
                if(self.cometLogic.addKMLSet == 0):
                    self.preComet()
                self.cometLogic.handleLine(
                    params[1], params[2], params[3], params[4])
                self.addLine(params[1], params[2], params[3], params[4], 0)
                # self.cometLogic.handleEndKML()
                if(self.cometLogic.addKMLSet == 0):
                    self.postComet()
            elif(params[0] == "endkml"):
                self.cometLogic.handleEndKML(0)
                self.postComet()
            elif(params[0] == "startkml"):
                self.preComet()
                self.cometLogic.startKML(0)

    def updateMapMetaData(self, ctrlat, ctrlng, zoom, showx, showy):
        self.NOW_MAP_CENTER_LAT = ctrlat
        self.NOW_MAP_CENTER_LNG = ctrlng
        self.NOW_MAP_ZOOM = zoom
        # calculate where to put media overlay
        showx = int(showx) + 60
        showy = int(showy) + 125
        if(showx > 60) and (showx < 700) and (showy > 125) and (showy < 400):
            # open media overlay
            if(self.mediaType == "photo"):
                # mediaWindow contains a photo
                self.mediaWindow.show()
                self.smartMove(
                    self.mediaWindow,
                    self.htmlScale * showx,
                    self.htmlScale * showy)
            else:
                # popWindow contains a video player
                self.popWindow.show()
                self.smartMove(
                    self.popWindow,
                    self.htmlScale * showx,
                    self.htmlScale * showy)
                self.popWindow.hide()
                self.mediaWindow.show_all()
        else:
            self.mediaWindow.hide()
            self.popWindow.hide()
        if(self.maptube is not None):
            # update XO group location
            self.maptube.SendText("loc," + ctrlat + "," + ctrlng + "," + zoom)

    def _trayMouseCb(self, events, args):
        if (self.shownRecd is not None):
            self.hideMedia()
            self.preComet()
            self.cometLogic.handleClear()
            self.postComet()

        return True

    # def loadMapV3(self):
    #    self.browser.load_uri("file://" + self.htmlPath + "/map3.html?ajaxPort=" + str(self.__class__.ajaxPort) + "&cometPort=" + str(self.__class__.cometPort) + "&xo=true" + "&lat=" + str(self.NOW_MAP_CENTER_LAT) + "&lng=" + str(self.NOW_MAP_CENTER_LNG) + "&zoom=" + str(self.NOW_MAP_ZOOM) + "&type=" + self.__class__.initType)

    def _tagsBufferEditedCb(self, widget):
        if (self.shownSave is not None):
            txt = self.tagsBuffer.get_text(
                self.tagsBuffer.get_start_iter(),
                self.tagsBuffer.get_end_iter())
            if (txt != self.shownSave.notes):
                self.shownSave.notes = txt

    def _hideInfoCb(self, butt):
        self.hideSearchResult()

    def hideSearchResult(self):
        #self.shownSave = None
        self.infoWindow.set_property("accept-focus", False)
        self.moveWinOffscreen(self.infoWindow)
        self.enableNavigation()

    def showFileLoadBlocker(self, show):
        if (show):
            self.smartMove(self.selectWindow, 0, 0)
            self.smartResize(
                self.selectWindow,
                Gdk.Screen.width(),
                Gdk.Screen.height())
        else:
            self.moveWinOffscreen(self.selectWindow)

    def _sizeAllocateCb(self, widget, event):
        self.toolbarbox.disconnect(self.toolbarbox_SIZE_ALLOCATE_ID)

        self.smartMove(
            self.loadingWindow,
            0,
            self.toolbarbox.get_allocation().height)
        self.loadingWindow.resize(
            Gdk.Screen.width(),
            Gdk.Screen.height() -
            self.toolbarbox.get_allocation().height)
        return False

    def remoteServerActive(self, loaded):
        if (self.loaded):
            return
        else:
            self.loaded = loaded
            # add search results from load_file
            for i in range(0, len(self.m.savedMaps)):
                smap = self.m.savedMaps[i]
                self.addThumb(smap, False)
            self.searchToolbar.set_sensitive(True)
            self.addToolbar.set_sensitive(True)
            browserW = self.browseBox.get_allocation().width
            browserH = self.browseBox.get_allocation().height
            self.smartResize(self.infoWindow, browserW, browserH)
            self.moveWinOffscreen(self.loadingWindow)

    def addToWindowStack(self, win, parent):
        self.windowStack.append(win)
        win.set_transient_for(parent)
        win.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        win.set_decorated(False)
        win.set_focus_on_map(False)
        win.set_property("accept-focus", False)

    def moveWinOffscreen(self, win):
        # we move offscreen to resize or else we get flashes on screen, and
        # setting hide() doesn't allow resize & moves
        offW = (Gdk.Screen.width() + 100)
        offH = (Gdk.Screen.height() + 100)
        self.smartMove(win, offW, offH)

    def smartMove(self, win, x, y):
        winLoc = win.get_position()
        if ((winLoc[0] != x) or (winLoc[1] != y)):
            win.move(int(x), int(y))
            return True
        else:
            return False

    def smartResize(self, win, w, h):
        winSize = win.get_size()
        if ((winSize[0] != w) or (winSize[1] != h)):
            win.resize(w, h)
            return True
        else:
            return False

    def preComet(self):
        self.cond.acquire()

    def postComet(self):
        self.cond.notifyAll()
        self.cond.release()
        time.sleep(.1)

    def read_file(self, file):
        serialize.fill_media_hash(file, self.m)

    def close(self):
        self.hide()
        activity.Activity.close(self)

    def write_file(self, file):
        dom = serialize.save_media_hash(self.m)
        xmlFile = open(file, "w")
        dom.writexml(xmlFile)
        xmlFile.close()

    def _addressUpdateCb(self, otets, address):
        if(address.find(',') != -1):
            if(len(address.split(',')) == 3):
                addSplit = address.split(',')
                if(addSplit[2] == 'm'):
                    # add a marker at this lat,lng
                    self.preComet()
                    self.cometLogic.handleAddMarker(
                        addSplit[0], addSplit[1], addSplit[0] + "," + addSplit[1], "magenta")
                    self.cometLogic.handleEndKML()
                    self.postComet()
                    self.addInfoMarker(
                        addSplit[0],
                        addSplit[1],
                        addSplit[0] +
                        "," +
                        addSplit[1],
                        "magenta",
                        True)
                    return

        elif(os.path.exists(self.libPath)):
            mp_address = address.lower().replace(' ', '').replace('-', '')
            zoom = "13"
            lat = "-190"
            lng = "-190"
            places = open(self.libPath + "Places.csv", 'r')
            for place in places:
                pData = place.split(',')
                pData[0] = pData[0].lower().replace(' ', '').replace('-', '')
                if(pData[0] == mp_address):
                    lat = pData[1]
                    lng = pData[2]
                    if(pData[3] != "-1"):
                        zoom = pData[3]
                    self.preComet()
                    self.cometLogic.handleReceivedMap(lat, lng, zoom)
                    self.postComet()
                    return

        self.preComet()
        self.cometLogic.handleAddressUpdate(address)
        self.postComet()

    def _searchUpdateCb(self, otets, tags):
        self.NOW_MAP_TAGS = tags
        self.preComet()
        self.cometLogic.handleTagSearch(tags)
        self.postComet()

    def _buttEastCb(self, butt):
        self.hideMedia()
        self.preComet()
        self.cometLogic.handleCompassUpdate("e")
        self.postComet()

    def _buttWestCb(self, butt):
        self.hideMedia()
        self.preComet()
        self.cometLogic.handleCompassUpdate("w")
        self.postComet()

    def _buttNorthCb(self, butt):
        self.hideMedia()
        self.preComet()
        self.cometLogic.handleCompassUpdate("n")
        self.postComet()

    def _buttSouthCb(self, butt):
        self.hideMedia()
        self.preComet()
        self.cometLogic.handleCompassUpdate("s")
        self.postComet()

    def _zoomInCb(self, butt):
        self.hideMedia()
        self.preComet()
        self.cometLogic.handleZoomUpdate("+")
        self.postComet()

    def _zoomOutCb(self, butt):
        self.hideMedia()
        self.preComet()
        self.cometLogic.handleZoomUpdate("-")
        self.postComet()

    def _saveSearchCb(self, otets):
        self._saveSearch()

    def _saveSearch(self):
        # 1st: cover up the tray when grabbing a screenshot
        # this will take a moment, so disable all buttons while we wait
        self.SAVING_SEARCH = True
        self.disableNavigation()
        self.savingSearchMediaLoc = self.mediaWindow.get_position()
        self.moveWinOffscreen(self.mediaWindow)
        self.hideTray(True)

    def hideTray(self, hide):
        if (hide):
            self.trayBox.set_current_page(self.fakeTrayIndex)
        else:
            self.trayBox.set_current_page(self.realTrayIndex)

    def _fakeTrayVisibleNotifyCb(self, widget, event):
        if self.SAVING_SEARCH:
            GLib.idle_add(self._saveSearch2)

    def _saveSearch2(self):
        # add SavedMap
        window = self.canvas.get_window()
        width, height = window.get_size()
        screenshot = Gdk.pixbuf_get_from_window(window, 0, 0, width, height)

        popW, popH = [self.popW + (2 * self.popB), self.popH + (2 * self.popB)]
        popScreenshot = Gdk.pixbuf_get_from_window(
            self.popWindow.get_window(), 0, 0, popW, popH)

        popLoc = self.popWindow.get_position()
        popLocX = popLoc[0]
        popLocY = popLoc[1] - self.toolbarbox.get_allocation().height
        popScreenshot.composite(screenshot,
                                # move the actual mini-canvas (but not its
                                # internals (?))
                                popLocX, popLocY,
                                popW, popH,  # actual size of the mini-canvas
                                # offx, y of the painting (irrespective of the
                                # mini-canvas)
                                popLocX, popLocY,
                                1, 1,  # scalex,y
                                GdkPixbuf.InterpType.BILINEAR, 255)

        screenshotPath = os.path.join(Instance.instancePath, "savedMap.jpg")
        screenshotPath = utils.getUniqueFilepath(screenshotPath, 0)
        screenshot.save(screenshotPath, "jpeg", {})

        smallHeight = 120
        smallWidth = (width * smallHeight) / height
        screenshotSmall = screenshot.scale_simple(
            smallWidth, smallHeight, GdkPixbuf.InterpType.NEAREST)
        screenshotSmallPath = os.path.join(
            Instance.instancePath, "savedMapThumb.jpg")
        screenshotSmallPath = utils.getUniqueFilepath(screenshotSmallPath, 0)
        screenshotSmall.save(screenshotSmallPath, "jpeg", {})

        sm = SavedMap(
            self.NOW_MAP_CENTER_LAT,
            self.NOW_MAP_CENTER_LNG,
            self.NOW_MAP_ZOOM,
            screenshotPath,
            screenshotSmallPath,
            "Describe the map",
            self.NOW_MAP_TAGS)
        if (self.shownRecd is not None):
            sm.addViewedRecd(
                self.shownRecd.datastoreId,
                self.shownRecd.latitude,
                self.shownRecd.longitude)

        self.m.addSavedMap(sm)
        self.addThumb(sm, True)

        self.hideTray(False)
        self.enableNavigation()
        self.smartMove(
            self.mediaWindow,
            self.savingSearchMediaLoc[0],
            self.savingSearchMediaLoc[1])

        if(self.maptube is not None):
            self.maptube.SendText("smap," +
                                  str(self.NOW_MAP_CENTER_LAT) +
                                  "," +
                                  str(self.NOW_MAP_CENTER_LNG) +
                                  "," +
                                  str(self.NOW_MAP_ZOOM) +
                                  ",Describe this map")

    def addLine(self, id, color, thickness, pts, isNew):
        self.m.setLine(id, color, thickness, pts)
        if((self.maptube is not None) and (isNew == 1)):
            self.maptube.SendText(
                "line," +
                id +
                "," +
                color +
                "," +
                thickness +
                "," +
                pts)

    def lineMode(self, type):
        self.preComet()
        self.cometLogic.lineMode(type)
        self.postComet()

    def addSavedMap(self, lat, lng, zoom, info, isNew):
        # add SavedMap received from internet or other XO, use Google Static
        # Maps
        window = self.canvas.window
        width, height = window.get_size()
        screenshotPath = os.path.join(Instance.instancePath, "savedMap.jpg")
        urllib.urlretrieve(
            "http://maps.google.com/staticmap?key=ABQIAAAAxkKtrWN5q-vPTLRVmO_r6RRFDCLHCbUG3VrjXnZmMRXvQdFL3RS-b-ld9hTrkIgQlYsxPQ1kYq6y9A&size=200x120&format=jpg&center=" +
            str(lat) +
            "," +
            str(lng) +
            "&zoom=" +
            str(
                int(zoom) -
                1),
            screenshotPath)
        smallHeight = 120
        smallWidth = 200
        sm = SavedMap(lat, lng, zoom, screenshotPath, screenshotPath, info, "")
        self.m.addSavedMap(sm)
        self.addThumb(sm, True)
        if(isNew):
            if(self.maptube is not None):
                # user created SaveMap, send to others
                self.maptube.SendText(
                    "smap," + lat + "," + lng + "," + zoom + "," + info)

    def addInfoMarker(self, lat, lng, info, icon, sendUpdate):
        # add/update InfoMarker in model
        self.m.setInfo(lat, lng, info, icon)
        if(sendUpdate):
            if(self.maptube is not None):
                # send added/updated info marker
                self.maptube.SendText(
                    "mar," + lat + "," + lng + "," + info + "," + icon)
        else:
            # put InfoMarker on own map
            self.preComet()
            self.cometLogic.handleAddMarker(lat, lng, info, icon)
            self.postComet()

    def removeThumb(self, sm):
        kids = self.tray.get_children()
        for i in range(0, len(kids)):
            if (kids[i].data == sm):
                self.tray.remove_item(kids[i])
                kids[i].cleanUp()
                kids[i].disconnect(kids[i].getButtClickedId())
                kids[i].setButtClickedId(0)
                if (sm == self.shownSave):
                    self.hideSearchResult()
        self.m.savedMaps.remove(sm)

    def addThumb(self, sm, forceScroll):
        butt = SavedButton(self, sm)
        BUTT_CLICKED_ID = butt.connect("clicked", self._thumbClickedCb, sm)
        butt.setButtClickedId(BUTT_CLICKED_ID)
        self.tray.add_item(butt, len(self.tray.get_children()))
        butt.show()
        if (forceScroll):
            self.tray.scroll_to_end()

    # 1 way to see a sr
    def _thumbClickedCb(self, button, smap):
        self.showSearchResult(smap)
        self.preComet()
        self.cometLogic.handleSavedMap(
            smap.lat, smap.lng, smap.zoom, smap.notes)
        self.postComet()

    def showSearchResult(self, smap):
        self.shownSave = smap
        self.updateSearchResultTags(smap)
        self.searchToolbar._setTagsString(smap.tags)

    def updateSearchResultTags(self, smap):
        self.shownSave = smap
        self.lngValueLabel.set_text(str(smap.lng))
        self.latValueLabel.set_text(str(smap.lat))
        self.tagsBuffer.set_text(smap.notes)

    def _fillInInfoWindow(self):
        hbox = Gtk.HBox()
        self.infoWindow.add(hbox)
        clr = Constants.color_grey
        inset = 10
        self.infoWindow.modify_bg(Gtk.StateType.NORMAL, clr.g_color)
        ltBox = Gtk.VBox()
        ltBox.set_border_width(inset)
        rtBox = Gtk.VBox()
        hbox.pack_start(ltBox, True, True, 0)
        hbox.pack_start(rtBox, False, False, 0)
        latHBox = Gtk.HBox()
        ltBox.pack_start(latHBox, False, False, 0)
        latLabel = Gtk.Label()
        latLabel.set_markup("<b>" + Constants.istr_latitude + "</b>")
        latLabel.set_alignment(0, .5)
        latHBox.pack_start(latLabel, False, False, 0)
        self.latValueLabel = Gtk.Label()
        self.latValueLabel.set_alignment(0, .5)
        latHBox.pack_start(self.latValueLabel, True, True, 0)
        fillb1 = Gtk.HBox()
        fillb1.set_size_request(inset, inset)
        ltBox.pack_start(fillb1, False, False, 0)
        lngHBox = Gtk.HBox()
        ltBox.pack_start(lngHBox, False, False, 0)
        lngLabel = Gtk.Label()
        lngLabel.set_markup("<b>" + Constants.istr_longitude + "</b>")
        lngLabel.set_alignment(0, .5)
        lngHBox.pack_start(lngLabel, False, False, 0)
        self.lngValueLabel = Gtk.Label()
        self.lngValueLabel.set_alignment(0, .5)
        lngHBox.pack_start(self.lngValueLabel, True, True, 0)
        fillb2 = Gtk.HBox()
        fillb2.set_size_request(inset, inset)
        ltBox.pack_start(fillb2, False, False, 0)
        tagLabelBox = Gtk.HBox()
        ltBox.pack_start(tagLabelBox, False, False, 0)
        tagsLabel = Gtk.Label()
        tagsLabel.set_markup("<b>" + Constants.istr_tags + "</b>")
        tagsLabel.set_alignment(0, .5)
        tagLabelBox.pack_start(tagsLabel, False, False, 0)
        tagBox = Gtk.HBox()
        self.tagsBuffer = Gtk.TextBuffer()
        self.tagsBuffer.set_text("please edit me!")
        self.tagsBuffer.connect('changed', self._tagsBufferEditedCb)
        self.tagsField = Gtk.TextView.new_with_buffer(self.tagsBuffer)
        ltBox.pack_start(self.tagsField, True, True, 0)
        rtFill = Gtk.VBox()
        rtFill.set_spacing(0)
        rtFill.set_border_width(0)
        rtBox.pack_start(rtFill, True, True, 0)
        buttImg = Gtk.Image()
        buttPixb = Constants.info_on_svg.get_pixbuf()
        buttImg.set_from_pixbuf(buttPixb)
        buttImg.show()
        rtButt = Gtk.Button()
        rtButt.set_image(buttImg)
        rtButt.modify_bg(Gtk.StateType.NORMAL, Constants.color_black.g_color)
        rtButt.modify_bg(Gtk.StateType.ACTIVE, Constants.color_black.g_color)
        rtButt.modify_bg(
            Gtk.StateType.INSENSITIVE,
            Constants.color_black.g_color)
        rtButt.set_relief(Gtk.ReliefStyle.NONE)
        rtButt.set_property('can-default', True)
        rtButt.set_property('can-focus', False)
        rtButt.set_property('yalign', 1)
        rtButt.set_size_request(75, 75)
        rtButt.connect("clicked", self._hideInfoCb)
        grr = Gtk.EventBox()
        grr.modify_bg(Gtk.StateType.NORMAL, Constants.color_black.g_color)
        grr.add(rtButt)
        rtBox.pack_start(grr, False, False, 0)
        hbox.show_all()

    def showSearchResultTags(self, smap):
        self.updateSearchResultTags(smap)

        # avoid popups lingering
        self.hideMedia()
        self.preComet()
        self.cometLogic.handleClear()
        self.postComet()
        self.disableNavigation()
        browserLoc = self.browseBox.translate_coordinates(self, 0, 0)
        self.infoWindow.show_all()
        self.smartMove(self.infoWindow, browserLoc[0], browserLoc[1])
        browserW = self.browseBox.get_allocation().width
        browserH = self.browseBox.get_allocation().height
        self.smartResize(self.infoWindow, browserW, browserH)
        self.infoWindow.set_property("accept-focus", True)

    def copyToClipboard(self, smap):
        tmpImgPath = self.doClipboardCopyStart(smap)
        Gtk.Clipboard().set_with_data(
            [('text/uri-list', 0, 0)], self._clipboardGetFuncCb, self._clipboardClearFuncCb, tmpImgPath)
        return True

    def doClipboardCopyStart(self, smap):
        tmpImgPath = utils.getUniqueFilepath(smap.imgPath, 0)
        shutil.copyfile(smap.imgPath, tmpImgPath)
        return tmpImgPath

    def doClipboardCopyCopy(self, tmpImgPath, selection_data):
        tmpImgUri = "file://" + tmpImgPath
        selection_data.set("text/uri-list", 8, tmpImgUri)

    def doClipboardCopyFinish(self, tmpImgPath):
        if (tmpImgPath is not None):
            if (os.path.exists(tmpImgPath)):
                os.remove(tmpImgPath)
        tmpImgPath = None

    def _clipboardGetFuncCb(self, clipboard, selection_data, info, data):
        self.doClipboardCopyCopy(data, selection_data)

    def _clipboardClearFuncCb(self, clipboard, data):
        self.doClipboardCopyFinish(data)

    def _addMediaCb(self, ot, datastoreOb):
        self.addMeToMapObj = datastoreOb
        self.hideMedia()
        self.preComet()
        self.cometLogic.handlePreAdd()
        self.postComet()

    def _addKMLCb(self, ot, datastoreOb):
        self.readKML(open(datastoreOb.file_path, 'r'))

    def readKML(self, kml):
        firstLine = kml.readline()
        if(firstLine.find('<?xml version="1.0" ?><map') == 0):
            # Offline Map or regular Map file without meta-data
            self.preComet()
            self.cometLogic.startKML(1)
            xmlarray = firstLine.split('>')
            for node in xmlarray:
                # if(node.find('<mapItem') == 0):
                    # picture marker
                if(node.find('<infoMarker') == 0):
                    # info marker
                    lat = node[node.find('lat="') + 5:len(node)]
                    lat = lat[0:lat.find('"')]
                    lng = node[node.find('lng="') + 5:len(node)]
                    lng = lng[0:lng.find('"')]
                    description = node[node.find('info="') + 6:len(node)]
                    description = description[0:description.find('"')]
                    icon = node[node.find('icon="') + 6:len(node)]
                    icon = icon[0:icon.find('"')]
                    self.cometLogic.handleAddMarker(
                        lat, lng, description, icon)
                    self.addInfoMarker(lat, lng, description, icon, True)
                elif(node.find('<line') == 0):
                    # line
                    lineColor = node[node.find('lcolor="') + 8:len(node)]
                    lineColor = lineColor[0:lineColor.find('"')]
                    lineID = node[node.find('lid="') + 5:len(node)]
                    lineID = lineID[0:lineID.find('"')]
                    ptStr = node[node.find('lpts="') + 6:len(node)]
                    ptStr = ptStr[0:ptStr.find('"')]
                    lineThick = node[node.find('lthickness="') + 12:len(node)]
                    lineThick = lineThick[0:lineThick.find('"')]
                    self.cometLogic.handleLine(
                        lineID, lineColor, lineThick, ptStr)
                    self.addLine(lineID, lineColor, lineThick, ptStr, 1)
                elif(node.find('<savedMap') == 0):
                    # saved map
                    lat = node[node.find('lat="') + 5:len(node)]
                    lat = lat[0:lat.find('"')]
                    lng = node[node.find('lng="') + 5:len(node)]
                    lng = lng[0:lng.find('"')]
                    notes = node[node.find('notes="') + 7:len(node)]
                    notes = notes[0:notes.find('"')]
                    zoom = node[node.find('zoom="') + 6:len(node)]
                    zoom = zoom[0:zoom.find('"')]
                    self.addSavedMap(lat, lng, zoom, notes, True)
            self.cometLogic.handleEndKML(1)
            self.postComet()
            return
        placename = None
        description = None
        kmlIcon = None
        lat = None
        lng = None
        coordList = None
        placemarkType = None
        lineType = None
        stillDescribing = False
        morePts = False
        dataTable = None
        isOSM = False
        isGeoRSS = False
        self.preComet()
        self.cometLogic.startKML(1)
        for kmlline in kml:
            if((kmlline.find('<osm') != -1) and (lat is None) and (lng is None) and (coordList is None)):
                # jump to osm
                isOSM = True
                break
            elif((kmlline.find('georss') != -1) and (lat is None) and (lng is None) and (coordList is None)):
                # jump to GeoRSS
                isGeoRSS = True
                break
            if(kmlline.find('<Point') != -1):
                placemarkType = 'info'
            elif(kmlline.find('<LineString') != -1):
                placemarkType = 'line'
                lineType = 'line'
            elif(kmlline.find('<Polygon') != -1):
                placemarkType = 'poly'
                lineType = 'poly'
            # elif(kmlline.find('<GroundOverlay') != -1):
            #    placemarkType = 'overlay'
            if(kmlline.find('<ExtendedData') != -1):
                dataTable = '<table>'
            elif(kmlline.find('</ExtendedData>') != -1):
                dataTable = dataTable + '</table>'
            if(dataTable is not None):
                if(kmlline.find('<Data') != -1):
                    dataTable = dataTable + '<tr>'
                if(kmlline.find('<Data name="') != -1):
                    dataTable = dataTable + "<td><b>" + \
                        kmlline[kmlline.find('<Data name="') + 12:kmlline.rfind('"')] + "</b></td>"
                if(kmlline.find('<value>') != -1):
                    dataTable = dataTable + "<td>" + \
                        kmlline[kmlline.find('<value>') + 7:kmlline.find('</value>')] + "</td>"
                elif(kmlline.find('</Data>') != -1):
                    dataTable = dataTable + '</tr>'

            if(kmlline.find('<coordinates>') != -1):
                if(placemarkType == 'info'):
                    lng = kmlline[kmlline.find(
                        '<coordinates>') + 13:kmlline.find(',')]
                    lat = kmlline[kmlline.find(',') + 1:kmlline.rfind(',')]
                else:
                    if(kmlline.find('</coordinates>') == -1):
                        morePts = True
                    kmlline = kmlline.replace(
                        '<coordinates>', '').replace(
                        '</coordinates>', '')
                    coordList = kmlline.split(' ')
            elif(morePts):
                if(kmlline.find('</coordinates>') != -1):
                    morePts = False
                    kmlline = kmlline.replace('</coordinates>', '')
                coordList.extend(kmlline.split(' '))

            if(kmlline.find('<name>') != -1):
                placename = kmlline[kmlline.find(
                    '<name>') + 6:kmlline.find('</name>')]
            if(kmlline.find('<description>') != -1):
                description = kmlline[kmlline.find(
                    '<description>') + 13:len(kmlline)]
                if(kmlline.find('</description>') == -1):
                    # need to read in more lines
                    stillDescribing = True
                else:
                    description = description[0:description.find(
                        '</description')]
                    if(description.find('<![CDATA[') != -1):
                        description = description.replace(
                            '<![CDATA[', '').replace(']]>', '')
            elif(stillDescribing):
                description = description + kmlline
                if(kmlline.find('</description>') != -1):
                    stillDescribing = False
                    description = description[0:description.find(
                        '</description')]
                    if(description.find('<![CDATA[') != -1):
                        description = description.replace(
                            '<![CDATA[', '').replace(']]>', '')
            if(kmlline.find('<Icon><href>') != -1):
                icon = kmlline[kmlline.find(
                    '<Icon><href>') + 12:kmlline.find('</href>')]
            if((kmlline.find('</Placemark>') != -1) or (kmlline.find('<Placemark>') != -1)):
                # finish this placemark
                if(lat is not None):
                    if(description is None):
                        description = ""
                    else:
                        description = description.replace(
                            "width:300", "width:60").replace(
                            "max-height:400", "max-height:80")
                    if(dataTable is not None):
                        description = dataTable + description
                    if(placename is not None):
                        description = '<h3>' + placename + '</h3>' + description
                    if(icon is None):
                        icon = "null"
                    self.cometLogic.handleAddMarker(
                        lat, lng, description, icon)
                    self.addInfoMarker(lat, lng, description, icon, True)
                if(coordList is not None):
                    ptList = []
                    maxInterval = 1
                    if(len(coordList) > 50):
                        maxInterval = int(len(coordList) / 50)
                    interval = 1
                    for pt in coordList:
                        ptloc = pt.split(',')
                        interval = interval - 1
                        if((len(ptloc) > 1) and (interval < 2)):
                            ptList.append(ptloc[1] + "|" + ptloc[0])
                            interval = maxInterval
                    if(lineType == 'line'):
                        lineID = str(random.getrandbits(128))
                        self.cometLogic.handleLine(
                            lineID, "B22222", "5", '|'.join(ptList))
                        self.addLine(
                            lineID, "B22222", "5", '|'.join(ptList), 1)
                    elif(lineType == 'poly'):
                        lineID = "poly-" + str(random.getrandbits(128))
                        self.cometLogic.handleLine(
                            lineID, "7CFC00", "5", '|'.join(ptList))
                        self.addLine(
                            lineID, "7CFC00", "5", '|'.join(ptList), 1)
                    # elif(placemarkType == 'overlay'):
                lat = None
                lng = None
                description = None
                placename = None
                placemarkType = None
                coordList = None
                dataTable = None
        if(isOSM):
            # read in an OSM style file
            osmNodes = {}
            readingInNodeID = None
            readingInWayID = None
            for osm in kml:
                if(osm.find('<node') != -1):
                    # point, which may be part of a line
                    nodeID = osm[osm.find('id=') + 4:len(osm)]
                    nodeID = nodeID[0:nodeID.find('"')]
                    nodeID = nodeID[0:nodeID.find("'")]
                    lat = osm[osm.find('lat=') + 5:len(osm)]
                    lat = lat[0:lat.find("'")]
                    lat = lat[0:lat.find('"')]
                    lng = osm[osm.find('lon=') + 5:len(osm)]
                    lng = lng[0:lng.find("'")]
                    lng = lng[0:lng.find('"')]
                    osmNodes[nodeID] = {
                        "latitude": lat,
                        "longitude": lng,
                        "inWay": False,
                        "isWay": False}
                    if(osm.find('/>') == -1):
                        readingInNodeID = nodeID
                elif(readingInNodeID is not None):
                    # reading in tag-values for the point
                    if(osm.find('</node>') != -1):
                        readingInNodeID = None
                    else:
                        if(osm.find('<tag') != -1):
                            tName = osm[osm.find('k=') + 3:len(osm)]
                            tName = tName[0:tName.find('"')]
                            tName = tName[0:tName.find("'")]
                            vName = osm[osm.find('v=') + 3:len(osm)]
                            vName = vName[0:vName.find('"')]
                            vName = vName[0:vName.find("'")]
                            osmNodes[readingInNodeID][tName] = vName
                elif(osm.find('<way') != -1):
                    # line, composed of multiple points
                    readingInWayID = osm[osm.find('id=') + 4:len(osm)]
                    readingInWayID = readingInWayID[0:readingInWayID.find('"')]
                    readingInWayID = readingInWayID[0:readingInWayID.find("'")]
                    osmNodes[readingInWayID] = {"isWay": True, "pts": []}
                elif(readingInWayID is not None):
                    # reading in node ids composing the line
                    if(osm.find('</way>') != -1):
                        readingInWayID = None
                    else:
                        if(osm.find('<nd') != -1):
                            nodeRef = osm[osm.find('ref=') + 5:len(osm)]
                            if(nodeRef.find('"') != -1):
                                nodeRef = nodeRef[0:nodeRef.find('"')]
                            else:
                                nodeRef = nodeRef[0:nodeRef.find("'")]
                            osmNodes[readingInWayID]["pts"].append(nodeRef)
                            osmNodes[nodeRef]["inWay"] = True
            # decide how to publish nodes
            for node in osmNodes:
                if(osmNodes[node]["isWay"]):
                    # line composed of points
                    ptList = []
                    for pID in osmNodes[node]["pts"]:
                        ptList.append(
                            osmNodes[pID]["latitude"] +
                            "|" +
                            osmNodes[pID]["longitude"])
                    lineID = str(random.getrandbits(128))
                    self.cometLogic.handleLine(
                        lineID, "B22222", "5", '|'.join(ptList))
                    self.addLine(lineID, "B22222", "5", '|'.join(ptList), 1)
                elif(osmNodes[node]["inWay"] == False):
                    # independent point
                    description = "<table>"
                    for tag in osmNodes[node]:
                        if(tag == "latitude"):
                            continue
                        elif(tag == "longitude"):
                            continue
                        elif(tag == "inWay"):
                            continue
                        elif(tag == "isWay"):
                            continue
                        else:
                            value = osmNodes[node][tag]
                            description = description + "<tr><td>" + tag + \
                                "</td><td>" + str(value) + "</td></tr>"
                    description = description + "</table>"
                    self.cometLogic.handleAddMarker(
                        osmNodes[node]["latitude"], osmNodes[node]["longitude"], description, "null")
                    self.addInfoMarker(
                        osmNodes[node]["latitude"],
                        osmNodes[node]["longitude"],
                        description,
                        "null",
                        True)
        elif(isGeoRSS):
            # scan in GeoRSS
            placeLink = None
            lat = None
            lng = None
            description = None
            placename = None
            stillDescribing = False
            # self.preComet()
            for rss in kml:
                if(rss.find('<title') != -1):
                    placename = rss[rss.find('>') + 1:rss.find('</title>')]
                if(rss.find('<link') != -1):
                    placeLink = rss[rss.find('>') + 1:rss.find('</link>')]
                if(rss.find('<georss:point') != -1):
                    latlng = rss[rss.find('>') +
                                 1:rss.find('</georss:point>')].split(' ')
                    lat = latlng[0]
                    lng = latlng[1]
                if(rss.find('<description>') != -1):
                    description = rss[rss.find('<description>') + 13:len(rss)]
                    if(rss.find('</description>') == -1):
                        # need to read in more lines
                        stillDescribing = True
                    else:
                        description = description[0:description.find(
                            '</description')]
                elif(stillDescribing):
                    description = description + rss
                    if(rss.find('</description>') != -1):
                        stillDescribing = False
                        description = description[0:description.find(
                            '</description')]
                if(rss.find('</item>') != -1):
                    # publish the point
                    if(lat is not None):
                        if(description is None):
                            description = ""
                        if(placeLink is not None):
                            description = placeLink + "<br/>" + description
                        if(placename is not None):
                            description = '<h3>' + placename + '</h3>' + description
                        description = description.replace(
                            "'", "\\'").replace('"', '\\"')
                        description = description.replace(
                            "\n", "<br/>").replace("\r", "<br/>")
                        description = description.replace(
                            "<![CDATA[", "").replace("]]>", "")
                        self.cometLogic.handleAddMarker(
                            lat, lng, description, "null")
                        self.addInfoMarker(lat, lng, description, "null", True)
                        placeLink = None
                        lat = None
                        lng = None
                        placename = None
                        description = None
                        stillDescribing = False
        self.cometLogic.handleEndKML(1)
        self.postComet()

    def _addInfoCb(self, ot):
        self.preComet()
        self.cometLogic.handlePreAddInfo()
        self.postComet()

    def _measureCb(self, ot):
        self.preComet()
        self.cometLogic.handleMeasure()
        self.postComet()

    def _olpcmapCb(self, ot):
        self.preComet()
        self.cometLogic.handleOlpcMAP()
        self.postComet()

    def _panoramioCb(self, ot):
        self.preComet()
        self.cometLogic.handlePanoramio()
        self.postComet()

    def _localwikiCb(self, ot):
        self.preComet()
        self.cometLogic.handleLocalWiki()
        self.postComet()

    def _wikimapiaCb(self, ot):
        self.preComet()
        self.cometLogic.handleWikiMapia()
        self.postComet()

    def disableNavigation(self):
        # disable the nav buttons
        self.buttEast.set_image(Constants.east_img_bw)
        self.buttEast.set_sensitive(False)
        self.buttWest.set_image(Constants.west_img_bw)
        self.buttWest.set_sensitive(False)
        self.buttNorth.set_image(Constants.north_img_bw)
        self.buttNorth.set_sensitive(False)
        self.buttSouth.set_image(Constants.south_img_bw)
        self.buttSouth.set_sensitive(False)
        # disable the toolbar buttons
        self.addToolbar.set_sensitive(False)
        self.searchToolbar.set_sensitive(False)

    def enableNavigation(self):
        # enable the nav buttons
        # self.buttEast.set_image(Constants.east_img_clr)
        # self.buttEast.set_sensitive(True)
        # self.buttWest.set_image(Constants.west_img_clr)
        # self.buttWest.set_sensitive(True)
        # self.buttNorth.set_image(Constants.northImgClr)
        # self.buttNorth.set_sensitive(True)
        # self.buttSouth.set_image(Constants.south_img_clr)
        # self.buttSouth.set_sensitive(True)
        # enable the toolbar buttons
        # self.addToolbar.set_sensitive(True)
        # self.searchToolbar.set_sensitive(True)
        pass

    def placeAddMedia(self, lat, lng):
        self.enableNavigation()
        # append to the map
        recd = self.m.addMedia(lat, lng, self.addMeToMapObj)
        # now show the new addition to the map
        self.preComet()
        self.cometLogic.handlePostAdd(recd)
        self.postComet()
        # send image to others
        # if(self.maptube is not None):
        #    self.maptube.SendText("mar," + lat + "," + lng + "," + utils.getStringFromPixbuf(recd.getPixBuf()))

    def sendEndKML(self):
        self.maptube.SendText("endkml,now")

    def sendStartKML(self):
        self.maptube.SendText("startkml,now")

    def _deleteMediaCb(self, ot):
        self.preComet()
        self.cometLogic.handleDelete()
        self.postComet()

    def showMedia(self, id, x, y, up, rt):
        recd = self.m.getMediaByThumbFilename(id)
        if (recd is None):
            return
        self.shownRecd = recd
        thumbPath = recd.getThumbPath()
        thumbPixbuf = GdkPixbuf.Pixbuf.new_from_file(thumbPath)
        px, py = [self.popW, self.popH]
        scl = (self.popW + 0.0) / (thumbPixbuf.get_width() + 0.0)
        thumbCairo = utils.generateThumbnail(thumbPixbuf, scl, px, py)
        self.popUpBg.updatePopInfo(
            recd.colorStroke,
            recd.colorFill,
            thumbCairo,
            up,
            rt,
            self.popB,
            self.popB,
            self.htmlScale)
        browserLoc = self.browseBox.translate_coordinates(self, 0, 0)
        x = int(x) * self.htmlScale
        y = int(y) * self.htmlScale
        x = browserLoc[0] + x
        y = browserLoc[1] + y
        if (not rt):
            x = x - (self.popW + (2 * self.popB))
        if (not up):
            y = y - (self.popH + (2 * self.popB))
        self.smartMove(self.popWindow, x, y)
        kid = self.mediaWindow.get_child()
        if (kid is not None):
            self.gplay.stop()
            self.mediaWindow.remove(kid)
        self.mediaWindow.modify_bg(
            Gtk.StateType.NORMAL,
            recd.colorFill.g_color)
        if (recd.type == Constants.TYPE_PHOTO):
            self.mediaType = 'photo'
            self.popWindow.hide()
            self.mediaWindow.show()
            self.smartResize(self.mediaWindow, self.popW, self.popH)
            self.smartMove(self.mediaWindow, x + self.popB, y + self.popB)
            pbuf = recd.getPixBuf()
            ##img = _camera.cairo_surface_from_gdk_pixbuf(pbuf)
            self.photoCanvas.modify_bg(
                Gtk.StateType.NORMAL, recd.colorFill.g_color)
            self.photoCanvas.set_size_request(self.popW, self.popH)
            # self.photoCanvas.setImage(img)
            self.mediaWindow.add(self.photoCanvas)
            self.photoCanvas.show_all()

        elif (recd.type == Constants.TYPE_VIDEO):
            self.mediaType = 'video'
            self.popWindow.show()
            self.mediaWindow.show()
            self.smartResize(self.mediaWindow, self.popW, self.popH)
            self.smartMove(self.mediaWindow, x + self.popB, y + self.popB)
            self.smartMove(self.popWindow, x + self.popB, y + self.popB)
            self.mediaWindow.add(self.gplayWin)
            self.gplayWin.modify_bg(
                Gtk.StateType.NORMAL,
                recd.colorFill.g_color)
            self.popWindow.hide()
            self.mediaWindow.show()
            self.gplayWin.show_all()
            videoUrl = "file://" + str(recd.getFilepath())
            self.gplay.setLocation(videoUrl)
            self.gplay.play()

    def hideMedia(self):
        self.shownRecd = None
        self.moveWinOffscreen(self.popWindow)
        self.moveWinOffscreen(self.mediaWindow)
        self.gplay.pause()

    def destroy(self, *args):
        self.hide()
        os._exit(0)  # needed to kill all threads
        Gtk.main_quit()

    def _shared_cb(self, activity):
        self.initiating = True
        self._sharing_setup()
        id = self.tubes_chan[telepathy.CHANNEL_TYPE_TUBES].OfferDBusTube(
            SERVICE, {})

    def _sharing_setup(self):
        if self._shared_activity is None:
            return
        self.conn = self._shared_activity.telepathy_conn
        self.tubes_chan = self._shared_activity.telepathy_tubes_chan
        self.text_chan = self._shared_activity.telepathy_text_chan
        self.tubes_chan[telepathy.CHANNEL_TYPE_TUBES].connect_to_signal(
            'NewTube', self._new_tube_cb)

    def _list_tubes_reply_cb(self, tubes):
        for tube_info in tubes:
            self._new_tube_cb(*tube_info)

    # joining a pre-existing activity
    def _joined_cb(self, activity):
        if not self._shared_activity:
            return
        self.initiating = False
        self._sharing_setup()
        self.tubes_chan[telepathy.CHANNEL_TYPE_TUBES].ListTubes(
            reply_handler=self._list_tubes_reply_cb, error_handler=self.tubes_error)

    # display error raised by XO-XO connection on map
    def tubes_error(self, e):
        self.preComet()
        self.cometLogic.handleCompassUpdate("Error: %s", e)
        self.postComet()

    def _new_tube_cb(self, id, initiator, type, service, params, state):
        if (type == telepathy.TUBE_TYPE_DBUS and service == SERVICE):
            if state == telepathy.TUBE_STATE_LOCAL_PENDING:
                self.tubes_chan[telepathy.CHANNEL_TYPE_TUBES].AcceptDBusTube(
                    id)
            tube_conn = TubeConnection(self.conn,
                                       self.tubes_chan[telepathy.CHANNEL_TYPE_TUBES],
                                       id,
                                       group_iface=self.text_chan[telepathy.CHANNEL_INTERFACE_GROUP])
            self.maptube = TextSync(
                tube_conn,
                self.initiating,
                self._received_cb,
                self.tubes_error,
                self._get_buddy)

    # _get_buddy may not be necessary.  Borrowed from HelloMesh
    def _get_buddy(self, cs_handle):
        group = self.text_chan[telepathy.CHANNEL_INTERFACE_GROUP]
        my_csh = group.GetSelfHandle()
        if my_csh == cs_handle:
            handle = self.conn.GetSelfHandle()
        elif group.GetGroupFlags() & telepathy.CHANNEL_GROUP_FLAG_CHANNEL_SPECIFIC_HANDLES:
            handle = group.GetHandleOwners([cs_handle])[0]
        else:
            handle = cs_handle
        return self.pservice.get_buddy_by_telepathy_handle(
            self.conn.service_name, self.conn.object_path, handle)


class TextSync(ExportedGObject):
    def __init__(self, tube, is_initiator, text_received_cb, alert, get_buddy):
        super(TextSync, self).__init__(tube, PATH)
        self.tube = tube
        self.is_initiator = is_initiator
        self.text_received_cb = text_received_cb
        self._alert = alert
        self.entered = False  # Have we set up the tube?
        self.text = ''  # State that gets sent or received
        self._get_buddy = get_buddy  # Converts handle to Buddy object
        self.tube.watch_participants(self.participant_change_cb)

    def participant_change_cb(self, added, removed):
        for handle, bus_name in added:
            buddy = self._get_buddy(handle)
        for handle in removed:
            buddy = self._get_buddy(handle)
        if not self.entered:
            if self.is_initiator:
                self.add_hello_handler()
            else:
                self.Hello()
        self.entered = True

    @signal(dbus_interface=IFACE, signature='')
    def Hello(self):
        self.bogus = 1

    @method(dbus_interface=IFACE, in_signature='s', out_signature='')
    def World(self, text):
        if not self.text:
            self.text = text
            self.text_received_cb(text)
            self.add_hello_handler()

    def add_hello_handler(self):
        self.tube.add_signal_receiver(self.hello_cb, 'Hello', IFACE,
                                      path=PATH, sender_keyword='sender')
        self.tube.add_signal_receiver(self.sendtext_cb, 'SendText', IFACE,
                                      path=PATH, sender_keyword='sender')

    def hello_cb(self, sender=None):
        if sender == self.tube.get_unique_name():
            return
        self.tube.get_object(sender, PATH).World(self.text,
                                                 dbus_interface=IFACE)

    def sendtext_cb(self, text, sender=None):
        if sender == self.tube.get_unique_name():
            return
        self.text = text
        self.text_received_cb(text)

    @signal(dbus_interface=IFACE, signature='s')
    def SendText(self, text):
        self.text = text


class SearchToolbar(Gtk.Toolbar):

    __gsignals__ = {
        'address-update': (GObject.SIGNAL_RUN_FIRST, None, [object]),
        'search': (GObject.SIGNAL_RUN_FIRST, None, [object]),
        'zoom-in': (GObject.SIGNAL_RUN_FIRST, None, []),
        'zoom-out': (GObject.SIGNAL_RUN_FIRST, None, []),
        'save-search': (GObject.SIGNAL_RUN_FIRST, None, []),
        'search-update': (GObject.SIGNAL_RUN_FIRST, None, [object])
    }

    def __init__(self, pc):
        Gtk.Toolbar.__init__(self)

        self.ca = pc

        addressLabel = Gtk.Label(Constants.istr_search_address)
        addressLabel.show()
        toolAddressLabel = Gtk.ToolItem()
        toolAddressLabel.add(addressLabel)
        self.insert(toolAddressLabel, -1)
        toolAddressLabel.show()

        self._insertSep()

        self.addressField = Gtk.Entry()
        self.addressField.connect('activate', self._addressActivateCb)
        addressItem = Gtk.ToolItem()
        addressItem.set_expand(True)
        addressItem.add(self.addressField)
        self.addressField.show()
        self.insert(addressItem, -1)
        addressItem.show()

        self._insertSep()
        self._insertSep()
        self._insertSep()
        self._insertSep()

        searchLabel = Gtk.Label(Constants.istr_search_media)
        searchLabel.show()
        toolSearchLabel = Gtk.ToolItem()
        toolSearchLabel.add(searchLabel)
        self.insert(toolSearchLabel, -1)
        toolSearchLabel.show()

        self._insertSep()

        self.searchField = Gtk.Entry()
        self.searchField.connect('activate', self._searchActivateCb)
        searchItem = Gtk.ToolItem()
        searchItem.set_expand(True)
        searchItem.add(self.searchField)
        self.searchField.show()
        self.insert(searchItem, -1)
        searchItem.show()

        self._insertSep()

        saveButt = ToolButton("save-search")
        saveButt.set_tooltip(Constants.istr_save_search)
        saveButt.connect('clicked', self._saveCb)
        self.insert(saveButt, -1)
        saveButt.show()

        self._insertSep()

        zout = ToolButton('map-icon-zoomOut')
        zout.set_tooltip(Constants.istr_zoom_out)
        self.insert(zout, -1)
        zout.connect('clicked', self._zoomOutCb)

        zin = ToolButton('map-icon-zoomIn')
        zin.set_tooltip(Constants.istr_zoom_in)
        self.insert(zin, -1)
        zin.connect('clicked', self._zoomInCb)

    def _setTagsString(self, tags):
        self.searchField.set_text(tags)

    def _insertSep(self):
        separator = Gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(False)
        separator.set_size_request(Constants.ui_dim_INSET, -1)
        self.insert(separator, -1)

    def _addressActivateCb(self, widget):
        address = widget.props.text
        self.emit('address-update', address)

    def _saveCb(self, widget):
        self.emit('save-search')

    def _searchActivateCb(self, widget):
        search = widget.props.text
        self.emit('search-update', search)

    def _zoomInCb(self, button):
        self.emit('zoom-in')

    def _zoomOutCb(self, button):
        self.emit('zoom-out')


class PopUpP5(P5):

    def __init__(self):
        P5.__init__(self)

        self.fill = None
        self.stroke = None
        self.previewCairoImg = None
        self.up = None
        self.rt = None
        self.scale = None
        self.insetX = 0
        self.insetY = 0

    def updatePopInfo(
            self,
            stroke,
            fill,
            cairoThumb,
            up,
            rt,
            insetX,
            insetY,
            scale):
        self.fill = fill
        self.stroke = stroke
        self.previewCairoImg = cairoThumb
        self.up = up
        self.rt = rt
        self.scale = scale
        self.insetX = insetX
        self.insetY = insetY
        self.queue_draw()

    def draw(self, ctx, w, h):
        # for stroking
        self.fillRect(ctx, self.fill, w, h)

        lw = 5
        hlw = lw / 2
        ctx.set_line_width(lw * self.scale)
        ctx.rectangle(0, 0, w, h)
        self.setColor(ctx, self.stroke)
        ctx.stroke()

        # for the popup bubble's handle
        if (not self.up):
            ctx.translate(0, h - (3 * self.scale))
        if (not self.rt):
            ctx.translate(w - ((hlw + 21) * self.scale), 0)
        else:
            ctx.translate(hlw * self.scale, 0)

        ctx.rectangle(0, 0, 21 * self.scale, 3 * self.scale)
        self.setColor(ctx, self.fill)
        ctx.fill()

        ctx.identity_matrix()
        ctx.set_source_surface(self.previewCairoImg, self.insetX, self.insetY)
        ctx.paint()


class AddToolbar(Gtk.Toolbar):

    __gsignals__ = {
        'add-media': (GObject.SIGNAL_RUN_FIRST, None, [object]),
        'add-kml': (GObject.SIGNAL_RUN_FIRST, None, [object]),
        'web-media': (GObject.SIGNAL_RUN_FIRST, None, []),
        'delete-media': (GObject.SIGNAL_RUN_FIRST, None, []),
        'measure': (GObject.SIGNAL_RUN_FIRST, None, []),
        'olpcmap': (GObject.SIGNAL_RUN_FIRST, None, []),
        'panoramio': (GObject.SIGNAL_RUN_FIRST, None, []),
        'local-wiki': (GObject.SIGNAL_RUN_FIRST, None, []),
        'wikimapia': (GObject.SIGNAL_RUN_FIRST, None, []),
        'add-info': (GObject.SIGNAL_RUN_FIRST, None, [])
    }

    def __init__(self, pc):
        Gtk.Toolbar.__init__(self)

        self.ca = pc

        self.addButt = ToolButton('add-icon')
        self.addButt.set_tooltip(Constants.istr_add_media)
        self.insert(self.addButt, -1)
        self.addButt.connect('clicked', self._addCb)

        infoButt = ToolButton('info-marker')
        infoButt.set_tooltip(Constants.istr_add_info)
        self.insert(infoButt, -1)
        infoButt.connect('clicked', self._addInfoCb)

        delButt = ToolButton('delete-icon')
        delButt.set_tooltip(Constants.istr_delete_media)
        self.insert(delButt, -1)
        delButt.connect('clicked', self._delCb)

        self._insertSep()

        # add line tools
        lineButt = ToolButton('tool-shape-line')
        lineButt.set_tooltip(Constants.line_button)
        self.insert(lineButt, -1)
        lineButt.connect('clicked', self._lineCb)
        polyButt = ToolButton('tool-polygon')
        polyButt.set_tooltip(Constants.poly_button)
        self.insert(polyButt, -1)
        polyButt.connect('clicked', self._polyCb)

        self._insertSep()

        measButt = ToolButton('measure-icon')
        measButt.set_tooltip(Constants.istr_measure)
        self.insert(measButt, -1)
        measButt.connect('clicked', self._measCb)

        self._insertSep()

        # Maps4xo library
        webButt = ToolButton('web-icon')
        webButt.set_tooltip(Constants.istr_web_media)
        self.insert(webButt, -1)
        webButt.connect('clicked', self._webCb)

        # OurMaps Wiki
        staticButt = ToolButton('static-icon')
        staticButt.set_tooltip(Constants.istr_static_maps)
        self.insert(staticButt, -1)
        staticButt.connect('clicked', self._toStaticCb)

        panorButt = ToolButton('panoramio')
        panorButt.set_tooltip(Constants.istr_panoramio)
        self.insert(panorButt, -1)
        panorButt.connect('clicked', self._toPanoramioCb)

        lwButt = ToolButton('localwiki')
        lwButt.set_tooltip(Constants.istr_local_wiki)
        self.insert(lwButt, -1)
        lwButt.connect('clicked', self._toLocalWikiCb)

        mapiaButt = ToolButton('wikimapia')
        mapiaButt.set_tooltip(Constants.istr_wiki_mapia)
        self.insert(mapiaButt, -1)
        mapiaButt.connect('clicked', self._toWikiMapiaCb)

    def _insertSep(self):
        separator = Gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(False)
        separator.set_size_request(25 + Constants.ui_dim_INSET, -1)
        self.insert(separator, -1)

    def _addCb(self, button):
        self.ca.showFileLoadBlocker(True)

        fp = FilePicker()
        dOb = fp.show()
        if (dOb is not None):
            if (dOb.file_path is not None):
                if(dOb.metadata['mime_type'] == "video/ogg") or (dOb.metadata['mime_type'] == "image/jpeg"):
                    self.emit("add-media", dOb)
                elif(dOb.metadata['mime_type'] == "audio/ogg"):
                    self.emit("add-media", dOb)
                else:
                    self.emit("add-kml", dOb)
                # else:
                #    self.emit("add-info")

        self.ca.showFileLoadBlocker(False)

    def _addInfoCb(self, button):
        self.emit("add-info")

    def _delCb(self, button):
        self.emit("delete-media")

    def _webCb(self, button):
        self.ca.browser.load_uri("http://maptonomy.appspot.com/maps4xo?ajaxPort=" +
                                 str(self.ca.__class__.ajaxPort) +
                                 "&cometPort=" +
                                 str(self.ca.__class__.cometPort) +
                                 "&xo=true&lat=" +
                                 str(self.ca.NOW_MAP_CENTER_LAT) +
                                 "&lng=" +
                                 str(self.ca.NOW_MAP_CENTER_LNG) +
                                 "&z=" +
                                 str(self.ca.NOW_MAP_ZOOM) +
                                 "&" +
                                 Constants.istr_lang)

    def _measCb(self, button):
        # start a measure tool (rect area or polyline) - calculation handled in
        # HTML/JavaScript
        self.emit("measure")

    def _toStaticCb(self, button):
        # Map wiki through maptonomy.appspot.com/ourmap.html
        #self.ca.browser.load_uri("http://maptonomy.appspot.com/ourmap.html?ajaxPort=" + str(self.ca.__class__.ajaxPort) + "&cometPort=" + str(self.ca.__class__.cometPort) + "&xo=true&lat=" + str(self.ca.NOW_MAP_CENTER_LAT) + "&lng=" + str(self.ca.NOW_MAP_CENTER_LNG) + "&zoom=" + str(self.ca.NOW_MAP_ZOOM) + "&" + Constants.istr_lang )
        self.emit("olpcmap")
        # self.ca.preComet()
        # self.ca.cometLogic.handleOlpcMAP()
        # self.ca.postComet()

    def _toPanoramioCb(self, button):
        self.emit("panoramio")

    def _toLocalWikiCb(self, button):
        self.emit("local-wiki")

    def _toWikiMapiaCb(self, button):
        self.emit("wikimapia")

    def _lineCb(self, button):
        self.ca.lineMode('line')

    def _polyCb(self, button):
        self.ca.lineMode('polygon')


class ServerThread(threading.Thread):

    def __init__(self, port, logic):
        threading.Thread.__init__(self)

        self.server = Server(("127.0.0.1", port), logic)

    def run(self):
        try:
            self.server.serve_forever()
        except BaseException:
            self.run()

    def stop(self):
        # self.server.shutdown()
        r = 2
