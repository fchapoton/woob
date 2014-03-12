# -*- coding: utf-8 -*-

# Copyright(C) 2013      Bezleputh
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

#from weboob.tools.browser.decorators import id2url
#from weboob.tools.browser import BaseBrowser
#from .calendar import HybrideCalendarEvent
from .pages import ProgramPage, EventPage


from weboob.tools.browser2 import PagesBrowser, URL, Firefox

__all__ = ['HybrideBrowser']


class HybrideBrowser(PagesBrowser):
    PROFILE = Firefox()
    BASEURL = 'http://www.lhybride.org'

    program_page = URL('/programme.html', ProgramPage)
    event_page = URL('/programme/item/(?P<_id>.*)', EventPage)

    def list_events(self, date_from, date_to=None, city=None, categories=None):
        self.program_page.stay_or_go()
        self.page.set_filters(date_from, date_to, city, categories)
        return self.page.list_events()

    def get_event(self, _id, event=None):
        return self.event_page.stay_or_go(_id=_id).get_event(obj=event)
