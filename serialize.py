#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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

import xml.dom.minidom
from xml.dom.minidom import getDOMImplementation
from xml.dom.minidom import parse
import cStringIO
import os

from gi.repository import Gtk

from sugar3.datastore import datastore

import utils
import recorded
from recorded import Recorded
from constants import Constants
from instance import Instance
from savedmap import SavedMap


def fill_media_hash(index, m):
    doc = None
    if os.path.exists(index):
        try:
            doc = parse(os.path.abspath(index))

        except:
            return

    try:
        last_lat = doc.documentElement.getAttributeNode(Constants.mapLat).nodeValue
        last_lng = doc.documentElement.getAttributeNode(Constants.mapLng).nodeValue
        last_zoom = doc.documentElement.getAttributeNode(Constants.mapZoom).nodeValue
        m.ca.preComet()
        m.ca.cometLogic.handleReceivedMap(last_lat, last_lng, last_zoom)
        m.ca.postComet()

    except:
        # likely an old saved map
        last_lat = 0

    recd_elements = doc.documentElement.getElementsByTagName(Constants.recd_map_item)
    for el in recd_elements:
        _load_media_into_hash(el, m)

    save_elements = doc.documentElement.getElementsByTagName(Constants.recd_saved_map_item)
    for el in save_elements:
        _load_saved_map(el, m)

    save_elements = doc.documentElement.getElementsByTagName(Constants.recd_info_marker)
    for el in save_elements:
        _load_info_marker(el, m)

    save_elements = doc.documentElement.getElementsByTagName(Constants.recd_line)
    for el in save_elements:
        _load_line(el, m)


def _load_saved_map(el, m):
    lat_node = el.getAttributeNode(Constants.recd_lat)
    lat = lat_node.nodeValue

    lng_node = el.getAttributeNode(Constants.recd_lng)
    lng = lng_node.nodeValue

    zoom_node = el.getAttributeNode(Constants.recd_zoom)
    zoom = zoom_node.nodeValue

    notes_node = el.getAttributeNode(Constants.recd_notes)
    notes = notes_node.nodeValue

    tags_node = el.getAttributeNode(Constants.recd_tags)
    tags = tags_node.nodeValue

    m.ca.addSavedMap(lat, lng, zoom, notes, False)


def _load_info_marker(el, m):
    lat_node = el.getAttributeNode(Constants.recd_lat)
    lat = lat_node.nodeValue

    lng_node = el.getAttributeNode(Constants.recd_lng)
    lng = lng_node.nodeValue

    infoNode = el.getAttributeNode(Constants.recd_info)
    info = info_node.nodeValue

    icon_node = el.getAttributeNode(Constants.recd_icon)
    icon = icon_node.nodeValue

    m.setInfo(lat,lng,info,icon)


def _load_line(el, m):
    id_node = el.getAttributeNode(Constants.line_id)
    id = idNode.nodeValue

    color_node = el.getAttributeNode(Constants.line_color)
    color = color_node.nodeValue

    thick_node = el.getAttributeNode(Constants.line_thick)
    thick = thick_node.nodeValue

    pts_node = el.getAttributeNode(Constants.line_pts)
    pts = pts_node.nodeValue

    m.setLine(id, color, thick, pts)


def _load_media_into_hash(el, m):
    if el.getAttributeNode(Constants.recd_datastore_id == None):
        return

    datastore_node = el.getAttributeNode(Constants.recd_datastore_id)

    if datastore_node != None:
        datastore_id = datastore_node.nodeValue
        if datastore_id != None:
            #quickly check: if you have a datastoreId that the file hasn't been deleted,
            #cause if you do, we need to flag your removal
            #2904 trac
            datastore_ob = get_media_from_datastore(datastore_id)
            if datastore_ob != None:

                lat = 0
                lng = 0

                if el.getAttributeNode(Constants.recd_lat) != None:
                    lat_node = el.getAttributeNode(Constants.recd_lat)
                    lat = lat_node.nodeValue

                else:
                    return

                if el.getAttributeNode(Constants.recd_lng) != None:
                    lng_node = el.getAttributeNode(Constants.recd_lng)
                    lng = lng_node.nodeValue

                else:
                    return

                m.addMedia(lat, lng, datastore_ob)


def get_media_from_datastore(id):
    media_object = None
    try:
        media_object = datastore.get(id)

    except:
        pass

    return media_object


def fill_recd_from_node(recd, el):
    lat_node = el.getAttributeNode(Constants.recd_lat)

    if lat_node != None:
        recd.latitude = lat_node.nodeValue

    lng_node = el.getAttributeNode(Constants.recd_lng)

    if lng_node != None:
        recd.longitude = lng_node.nodeValue

    return recd


def _add_recd_xml_attrs(el, recd):
    el.setAttribute(Constants.recd_datastore_id, str(recd.datastoreId))
    el.setAttribute(Constants.recd_lat, str(recd.latitude))
    el.setAttribute(Constants.recd_lng, str(recd.longitude))


def _add_info_xml_attrs(el, recd):
    el.setAttribute(Constants.recd_info, recd[2])
    el.setAttribute(Constants.recd_icon, recd[3])
    el.setAttribute(Constants.recd_lat, str(recd[0]))
    el.setAttribute(Constants.recd_lng, str(recd[1]))


def _add_line_xml_attrs(el, recd):
    el.setAttribute(Constants.line_id, recd[0])
    el.setAttribute(Constants.line_color, recd[1])
    el.setAttribute(Constants.line_thick, recd[2])
    el.setAttribute(Constants.line_pts, recd[3])


def _add_save_xml_attrs(el, smap):
    el.setAttribute(Constants.recd_lat, str(smap.lat))
    el.setAttribute(Constants.recd_lng, str(smap.lng))
    el.setAttribute(Constants.recd_zoom, str(smap.zoom))
    el.setAttribute(Constants.recd_notes, str(smap.notes))
    el.setAttribute(Constants.recd_tags, smap.tags)
    #el.setAttribute(Constants.recdDensity, str(smap.density))

    if smap.recdDatastoreId != None:
        el.setAttribute(Constants.recd_recd_id, smap.recdDatastoreId)
        el.setAttribute(Constants.recd_recd_lat, smap.recd_lat)
        el.setAttribute(Constants.recd_recd_lng, smap.recd_lng)


def save_media_hash(m):
    impl = getDOMImplementation()
    album = impl.createDocument(None, Constants.recd_album, None)
    root = album.documentElement

    for i in range (0, len(m.recs)):
        recd = m.recs[i]
        media_el = album.createElement(Constants.recd_map_item)
        root.appendChild(media_el)
        _add_recd_xml_attrs(media_el, recd)

    for k, i_marker in m.infoMarkers.iteritems():
        media_el = album.createElement(Constants.recd_info_marker)
        root.appendChild(media_el)
        _add_info_xml_attrs(media_el, i_marker.split(";~"))

    for k, i_marker in m.lineData.iteritems():
        media_el = album.createElement(Constants.recd_line)
        root.appendChild(media_el)
        _add_line_xml_attrs(media_el, i_marker.split(";~"))

    for i in range (0, len(m.savedMaps)):
        smap = m.savedMaps[i]
        save_el = album.createElement(Constants.recd_saved_map_item)
        root.appendChild(saveEl)
        _add_save_xml_attrs(save_el, smap)

    return album

