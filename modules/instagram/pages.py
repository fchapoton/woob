# -*- coding: utf-8 -*-

# Copyright(C) 2020      Vincent A
#
# This file is part of a weboob module.
#
# This weboob module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This weboob module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this weboob module. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re

from weboob.browser.elements import method, DictElement, ItemElement
from weboob.browser.filters.json import Dict
from weboob.browser.filters.standard import FromTimestamp
from weboob.browser.pages import HTMLPage, JsonPage
from weboob.capabilities.image import BaseImage, Thumbnail
from weboob.capabilities.file import LICENSES


class image_element(ItemElement):
    klass = BaseImage

    obj_id = Dict('node/id')

    obj_title = obj_id
    obj_ext = 'jpg'
    obj_license = LICENSES.COPYRIGHT

    obj_date = FromTimestamp(Dict('node/taken_at_timestamp'))
    obj_description = Dict('node/accessibility_caption', default=None)
    obj_url = Dict('node/display_url')

    def obj_thumbnail(self):
        return Thumbnail(Dict('node/thumbnail_src')(self))


class ListPageMixin:
    def get_end_cursor(self):
        if not self.subdoc['edge_owner_to_timeline_media']['page_info']['has_next_page']:
            return
        return self.subdoc['edge_owner_to_timeline_media']['page_info']['end_cursor']


class HomePage(ListPageMixin, JsonPage):
    def build_doc(self, text):
        text = re.search(r'_sharedData = (\{.*?\});</script', text)[1]
        return super().build_doc(text)

    @property
    def subdoc(self):
        return self.doc['entry_data']['ProfilePage'][0]['graphql']['user']

    def get_csrf(self):
        return self.doc['config']['csrf_token']

    def get_user_id(self):
        return self.subdoc['id']

    def get_author_name(self):
        return self.subdoc['full_name']

    @method
    class iter_images(DictElement):
        item_xpath = 'entry_data/ProfilePage/0/graphql/user/edge_owner_to_timeline_media/edges'

        item = image_element


class OtherPage(ListPageMixin, JsonPage):
    @property
    def subdoc(self):
        return self.doc['data']['user']

    @method
    class iter_images(DictElement):
        item_xpath = 'data/user/edge_owner_to_timeline_media/edges'

        item = image_element
