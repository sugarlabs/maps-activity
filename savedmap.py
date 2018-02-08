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


class SavedMap:

    def __init__(self, lat, lng, zoom, img_file, thumb_file, notes, tags):

        self.lat = lat
        self.lng = lng
        self.zoom = zoom
        self.img_path = img_file
        self.thumb_path = thumb_file
        self.notes = notes
        self.tags = tags
        self.density = " "

        self.recd_datastore_id = None
        self.recd_lat = None
        self.recd_lng = None

    def addViewedRecd(self, id, lat, lng):
        self.recd_datastore_id = id
        self.recd_lat = lat
        self.recd_lng = lng
