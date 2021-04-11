# -*- coding: utf-8 -*-

# Copyright(C) 2012 Florent Fourcot
#
# This file is part of a woob module.
#
# This woob module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This woob module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this woob module. If not, see <http://www.gnu.org/licenses/>.
"backend for http://www.taz.de"

from woob.capabilities.messages import CapMessages
from woob.tools.backend import AbstractModule
from .browser import NewspaperTazBrowser
from .tools import rssid, url2id


class NewspaperTazModule(AbstractModule, CapMessages):
    MAINTAINER = u'Florent Fourcot'
    EMAIL = 'weboob@flo.fourcot.fr'
    VERSION = '3.1'
    LICENSE = 'AGPLv3+'
    STORAGE = {'seen': {}}
    NAME = 'taz'
    DESCRIPTION = u'Taz newspaper website'
    BROWSER = NewspaperTazBrowser
    RSSID = staticmethod(rssid)
    URL2ID = staticmethod(url2id)
    RSSSIZE = 30
    RSS_FEED = "http://www.taz.de/!p3270;rss/"
    PARENT = 'genericnewspaper'
