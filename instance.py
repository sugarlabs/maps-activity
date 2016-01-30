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

from sugar3 import profile
from sugar3 import util
from sugar3.activity import activity
import shutil

from color import Color

class Instance:

    key = profile.get_pubkey()
    #joyride ...
    #keyHash = util.sha_data(key)
    #8.2...
    #keyHash = util._sha_data(key)
    #keyHashPrintable = util.printable_hash(keyHash)
    nick_name = profile.get_nick_name()

    color_fill = Color()
    color_fill.init_hex(profile.get_color().get_fill_color())
    color_stroke = Color()
    color_stroke.init_hex(profile.get_color().get_stroke_color())

    instance_id = None
    instance_path = None
    data_path = None

    def __init__(self, ca):
        self.__class__.instance_id = ca._activity_id

        self.__class__.instance_path = os.path.join(ca.get_activity_root(), "instance")
        recreate_tmp()

        self.__class__.data_path = os.path.join(ca.get_activity_root(), "data")
        recreate_data()


def recreate_tmp():
    if not os.path.exists(Instance.instance_path):
        os.makedirs(Instance.instancePath)


def recreate_data():
    if not os.path.exists(Instance.data_path):
        os.makedirs(Instance.data_dath)

