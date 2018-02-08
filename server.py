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

import urlparse
import urllib
import posixpath
import SimpleHTTPServer
import BaseHTTPServer


class Server(BaseHTTPServer.HTTPServer):

    def __init__(self, server_address, logic):
        BaseHTTPServer.HTTPServer.__init__(self, server_address, RegHandler)

        self.logic = logic


# RegHandler extends SimpleHTTPServer.py (in python 2.4)
class RegHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_POST(self):
        self.translate_path()

    def do_GET(self):
        self.translate_path()

    def do_HEAD(self):
        self.translate_path()

    def translate_path(self):
        # todo: compare with send_head in parent
        urlp = urlparse.urlparse(self.path)

        urls = urlp[2]
        urls = posixpath.normpath(urllib.unquote(urls))
        url_path = urls.split('/')
        url_path = filter(None, url_path)

        params = urlp[4]
        parama = []
        all_params = params.split('&')
        for i in range(0, len(all_params)):
            parama.append(all_params[i].split('='))

        result = self.server.logic.do_server_logic(self.path, url_path, parama)
        self.send_response(200)

        for i in range(0, len(result.headers)):
            self.send_header(result.headers[i][0], result.headers[i][1])

        self.end_headers()
        self.wfile.write(result.txt)
