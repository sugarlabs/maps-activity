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

from result import ServerResult
from instance import Instance

import os
import time
import urllib
import json

from gi.repository import GObject


class ServerLogic:

    def __init__(self, ca):
        self.ca = ca
        self.proceed_txt = ""
        self.proceed_headers = []
        self.cond = ca.cond
        self.add_kml_set = 0

    def do_server_logic(self, url, path, params):
        self.ca.remoteServerActive(True)
        r = ServerResult()
        file_name = path[len(path) - 1]

        if file_name == "comet.js":

            # clear...
            self.proceed_headers = []
            self.proceed_txt = ""

            # wait...
            self.cond.acquire()
            self.cond.wait()
            self.cond.release()

            # prep response...
            for h in range(len(self.proceed_headers)):
                r.headers.append(self.proceed_headers[h])

            # r.txt = ""+self.proceed_txt
            # self.ca.browser.load_uri("javascript:"+r.txt+"void(0);")

        else:
            kick_through_comet = True

            if (file_name == "mediaQuery.js"):
                self.proceed_headers.append(
                    ("Content-type", "text/javascript"))
                self.proceed_txt = self.ca.m.getMediaResponse(
                    params[0][1], params[1][1], params[2][1], params[3][1])

            elif (file_name == "showMedia.js"):
                id = params[0][1]
                locX = params[1][1]
                locY = params[2][1]
                up = params[3][1]
                rt = params[4][1]
                GObject.idle_add(
                    self.ca.showMedia,
                    id,
                    locX,
                    locY,
                    up == 'true',
                    rt == 'true')
                self.proceed_headers.append(
                    ("Content-type", "text/javascript"))

            elif (file_name == "placeAddMedia.js"):
                lat = params[0][1]
                lng = params[1][1]
                GObject.idle_add(self.ca.placeAddMedia, lat, lng)
                self.proceed_headers.append(
                    ("Content-type", "text/javascript"))
                kick_through_comet = False

            elif (file_name == "hideMedia.js"):
                GObject.idle_add(self.ca.hideMedia)

            elif (file_name == "getImage.js"):
                localfile = open(
                    os.path.join(
                        Instance.instancePath,
                        params[0][1]),
                    'r')
                localdata = localfile.read()
                localfile.close()

                # one day we might need to kick you through comet as a base64'd
                # image.
                r.txt = localdata
                r.headers.append(("Content-type", "image/jpeg"))
                kick_through_comet = False

            elif (file_name == "updateLocation.js"):
                lat = params[0][1]
                lng = params[1][1]
                zoom = params[2][1]
                x = params[3][1]
                y = params[4][1]
                GObject.idle_add(
                    self.ca.updateMapMetaData, lat, lng, zoom, x, y)

            elif (file_name == "addSavedMap.js"):
                # allow internet to send an array of SavedMaps back to map.py
                latitudes = params[0][1]
                longitudes = params[1][1]
                zooms = params[2][1]
                notes = params[3][1]
                GObject.idle_add(
                    self.ca.addSavedMap,
                    latitudes,
                    longitudes,
                    zooms,
                    urllib.unquote(notes),
                    True)

            elif (file_name == "addInfoMarker.js"):
                lat = params[0][1]
                lng = params[1][1]
                info = params[2][1]
                icon = params[3][1]
                if(params[4][1] == "True"):
                    isNew = True
                    GObject.idle_add(self.ca.cometLogic.forceupdate)
                else:
                    isNew = False

                GObject.idle_add(
                    self.ca.addInfoMarker, lat, lng, info, icon, isNew)

            elif (file_name == "addLine.js"):
                id = params[0][1]
                color = params[1][1]
                thickness = params[2][1]
                pts = params[3][1]  # send pts separated with | instead of ,
                GObject.idle_add(self.ca.addLine, id, color, thickness, pts, 1)

            elif (file_name == "promptSearch.js"):
                address = params[0][1]
                time.sleep(0.5)
                self.ca.preComet()
                self.handle_address_update(address + "+")
                self.ca.postComet()

            # elif (file_name == "gotoMapV3.js"):
                # button on static maps links to mapv3
                # self.ca.loadMapV3()

            if (kick_through_comet):
                # not sure how & why this goes out, but it does.
                self.cond.acquire()
                self.cond.notifyAll()
                self.cond.release()
                time.sleep(.1)

        return r

    def handle_address_update(self, address):
        findsrc = "http://maps.googleapis.com/maps/api/geocode/json?sensor=false&address=" + \
            urllib.quote(address)
        find_address = json.loads(urllib.urlopen(findsrc).read())

        longname = find_address["results"][0]["address_components"][0]["long_name"]

        swlat = find_address["results"][0]["geometry"]["bounds"]["southwest"]["lat"]
        swlng = find_address["results"][0]["geometry"]["bounds"]["southwest"]["lng"]

        nelat = find_address["results"][0]["geometry"]["bounds"]["northeast"]["lat"]
        nelng = find_address["results"][0]["geometry"]["bounds"]["northeast"]["lng"]

        self.proceed_headers.append(("Content-type", "text/javascript"))
        #self.proceed_txt = "showInfo('" + swlat + "," + swlng + "," + nelat + "," + nelng + "');"
        self.proceed_txt = "moveToAddress(" + str(swlat) + "," + str(
            swlng) + "," + str(nelat) + "," + str(nelng) + ",'" + longname + "');"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def forceupdate(self):
        # self.ca.preComet()

        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = "canvas.updateImg();"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")
        # self.ca.postComet()

    def handleCompassUpdate(self, dir):
        self.proceed_headers.append(("Content-type", "text/javascript"))

        if (dir == "e"):
            self.proceed_txt = "dirEast();"

        elif (dir == "w"):
            self.proceed_txt = "dirWest();"

        elif (dir == "n"):
            self.proceed_txt = "dirNorth();"

        elif (dir == "s"):
            self.proceed_txt = "dirSouth();"

        else:
            # use this as a print warning window
            self.proceed_txt = 'showInfo("' + dir + '");'

        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def handlePanoramio(self):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = 'panoramio();'
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def handleLocalWiki(self):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = 'wikiloc();'
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def handleWikiMapia(self):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = 'wikimapia();'
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def handleOlpcMAP(self):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        llc = [
            float(
                self.ca.NOW_MAP_CENTER_LAT), float(
                self.ca.NOW_MAP_CENTER_LNG)]
        llz = float(self.ca.NOW_MAP_ZOOM)
        lln = llc[0] + 0.55618 * 0.75 * (2 ** (9 - llz))
        lle = llc[1] + 0.98877 * 0.75 * (2 ** (9 - llz))
        lls = llc[0] - 0.55618 * 0.75 * (2 ** (9 - llz))
        llw = llc[1] - 0.98877 * 0.75 * (2 ** (9 - llz))

        findsrc = "http://mapmeld.appspot.com/olpcMAP/kml?llregion=" + \
            str(lln) + "," + str(lle) + "," + str(lls) + "," + str(llw)
        self.ca.readKML(urllib.urlopen(findsrc))

    def handleZoomUpdate(self, dir):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        if (dir == "+"):
            self.proceed_txt = "zoomIn();"

        elif (dir == "-"):
            self.proceed_txt = "zoomOut();"

        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def handleClear(self):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = "clear();"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def handlePreAdd(self):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = "preAddMedia();"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def handlePreAddInfo(self):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = "preAddInfo();"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def handlePostAdd(self, rec):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = "postAddMedia(" + rec.latitude + ", " + rec.longitude + ", '" + \
            rec.getThumbUrl() + "', '" + rec.getThumbBasename() + "', '" + rec.tags + "');"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def handleDelete(self):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = "deleteMedia();"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    # handle a map that was sent to us
    def handleReceivedMap(self, lat, lng, zoom):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = "setMap(" + lat + "," + lng + "," + zoom + ");"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def handleSavedMap(self, lat, lng, zoom, info):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        if(info.find("Describe the map") != 0):
            self.proceed_txt = "setMap2(" + lat + "," + lng + \
                "," + zoom + ",'" + urllib.quote(info) + "');"
        else:
            self.proceed_txt = "setMap2(" + lat + \
                "," + lng + "," + zoom + ",'');"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    # handle a marker that was sent to us
    def handleAddMarker(self, lat, lng, pixString, icon):
        if(self.addKMLSet < 1):
            self.proceed_headers.append(("Content-type", "text/javascript"))
            self.proceed_txt = ""
            if(self.addKMLSet == -1):
                self.addKMLSet = 1
        self.proceed_txt = self.proceed_txt + \
            "addInfoMarker(" + lat + ", " + lng + ", '" + pixString.replace("'", '"') + "', '" + icon + "',false);"
        #self.proceed_txt = self.proceed_txt + "addInfoMarker(" + lat + ", " + lng + ", '"+pixString.replace("'",'"')+"', 'http://mapmeld.appspot.com/xo-red.png',false);"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def startKML(self, tellOthers):
        self.addKMLSet = -1
        if((self.ca.maptube is not None) and (tellOthers == 1)):
            self.ca.sendStartKML()

    def handleEndKML(self, tellOthers):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = self.proceed_txt + "canvas.updateImg();"
        self.addKMLSet = 0
        if((self.ca.maptube is not None) and (tellOthers == 1)):
            self.ca.sendEndKML()

        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def lineMode(self, type):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = "lineMode('" + type + "');"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def handleLine(self, id, color, thickness, pts):
        if(self.addKMLSet < 1):
            self.proceed_headers.append(("Content-type", "text/javascript"))
            self.proceed_txt = ""
            if(self.addKMLSet == -1):
                self.addKMLSet = 1

        self.proceed_txt = self.proceed_txt + \
            "addLine('" + id + "','" + color + "','" + thickness + "','" + pts + "');"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    # handle start of measure tool
    def handleMeasure(self):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = "measure();"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")

    def handleTagSearch(self, tags):
        self.proceed_headers.append(("Content-type", "text/javascript"))
        self.proceed_txt = "filterTags('" + tags + "');"
        self.ca.ajaxServer.stop()
        self.ca.cometServer.stop()
        self.ca.browser.load_uri(
            "javascript:" +
            self.proceed_txt +
            ";void(0);")
