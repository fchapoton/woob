# -*- coding: utf-8 -*-

# Copyright(C) 2012 Lucien Loiseau
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


from woob.browser import PagesBrowser, URL

from .pages import TranslatePage
from .gtts_token import Token

__all__ = ['GoogleTranslateBrowser']


class GoogleTranslateBrowser(PagesBrowser):
    BASEURL = 'https://translate.google.fr'

    translate_page = URL('/translate_a/single\?client=t&sl=(?P<source>.*)&tl=(?P<to>.*)&dt=t&tk=(?P<token>.*)&q=(?P<text>.*)&ie=UTF-8&oe=UTF-8',
                         TranslatePage)

    def translate(self, source, to, text):
        """
        translate 'text' from 'source' language to 'to' language
        """
        t = text
        tk = Token(self).calculate_token(t)
        return self.translate_page.go(source=source,
                                      to=to,
                                      text=t,
                                      token=tk).get_translation()
