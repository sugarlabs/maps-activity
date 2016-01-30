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

import os
import map

from gi.repository import Gtk
from gi.repository import GdkPixbuf

from constants import Constants
from instance import Instance


class Recorded:

    SOURCE_DATASTORE = 0
    SOURCE_LOCAL = 1
    SOURCE_BUNDLE = 2

    def __init__(self):

        self.name = None
        self.recorded = None
        self.color_stroke = None
        self.color_fill = None
        self.type = None

        self.latitude = None
        self.longitude = None

        self.thumb_filename = None
        self.file_name = None
        self.datastore_ob = None
        self.datastore_id = None
        self.tags = ""

        self.source = 0

    def get_filepath(self):
        if (self.source == self.__class__.SOURCE_BUNDLE):
            path = os.path.join(Constants.html_path, self.file_name)
            return path

        elif (self.source == self.__class__.SOURCE_DATASTORE):
            return self.datastore_ob.file_path

        else:
            return None

    def get_pixbuf(self):
        pb = None

        fp = self.get_filepath()
        if (fp != None):
            pb = GdkPixbuf.Pixbuf.new_from_file(fp)

        return pb

    def getThumbUrl(self):
        return "http://127.0.0.1:" + str(map.Map.ajaxPort) + "/getImage.js?id="

    def getThumbBasename(self):
        return str(self.thumb_filename)

    def getThumbPath(self):
        thumbPath = os.path.join( Instance.instancePath, self.getThumbBasename() )
        return thumbPath

