# -*- coding: utf-8 -*-

# Copyright(C) 2017      Antoine BOSSY
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

from weboob.tools.backend import Module
from weboob.capabilities.housing import CapHousing

from .browser import FnaimBrowser

__all__ = ['FnaimModule']


class FnaimModule(Module, CapHousing):
    NAME = 'fnaim'
    DESCRIPTION = 'www.fnaim.fr website'
    MAINTAINER = 'Antoine BOSSY'
    EMAIL = 'mail+github@abossy.fr'
    LICENSE = 'AGPLv3+'
    VERSION = '1.4'

    BROWSER = FnaimBrowser

    def get_housing(self, housing):
        """
        Get an housing from an ID.

        :param housing: ID of the housing
        :type housing: str
        :rtype: :class:`Housing` or None if not found.
        """
        return self.browser.get_housing(housing)

    def search_city(self, pattern):
        """
        Search a city from a pattern.

        :param pattern: pattern to search
        :type pattern: str
        :rtype: iter[:class:`City`]
        """
        return self.browser.search_city(pattern)

    def search_housings(self, query):
        """
        Search housings.

        :param query: search query
        :type query: :class:`Query`
        :rtype: iter[:class:`Housing`]
        """
        return self.browser.search_housings(query)
