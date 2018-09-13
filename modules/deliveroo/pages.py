# -*- coding: utf-8 -*-

# Copyright(C) 2012-2022  Budget Insight
#
# This file is part of a woob module.
#
# This woob module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This woob module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this woob module. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import json

from weboob.browser.pages import HTMLPage, LoggedPage, pagination
from weboob.browser.elements import ItemElement, ListElement, method
from weboob.browser.filters.standard import CleanText, CleanDecimal, Env, Regexp, Format, Async, AsyncLoad
from weboob.browser.filters.html import Link, Attr
from weboob.capabilities.bill import Bill, Subscription
from weboob.capabilities.base import NotAvailable
from weboob.tools.date import parse_french_date
from weboob.tools.compat import urljoin


def MyDecimal(*args, **kwargs):
    kwargs.update(replace_dots=True, default=NotAvailable)
    return CleanDecimal(*args, **kwargs)


class HomePage(HTMLPage):
    pass


class LoginPage(HTMLPage):
    def get_csrf_token(self):
        return Attr('//meta[@name="csrf-token"]', 'content')(self.doc)


class ProfilPage(LoggedPage, HTMLPage):
    @method
    class get_item(ItemElement):
        klass = Subscription

        obj_subscriber = CleanText(Env('subscriber'))
        obj_id = CleanText(Env('id'))

        def obj_label(self):
            return self.page.browser.username

        def parse(self, el):
            data = Regexp(CleanText('//script[contains(., "ROO_PAGE_DATA")]'), r'var ROO_PAGE_DATA = (.*?);')(self)
            user = json.loads(data).get('user')

            self.env['id'] = str(user.get('id'))
            self.env['subscriber'] = user.get('full_name')


class DocumentsPage(LoggedPage, HTMLPage):
    @pagination
    @method
    class get_documents(ListElement):
        item_xpath = '//ul[has-class("user--history-list")]/li/a'

        next_page = Link('//a[@class="pagination-link next"]', default=None)

        class item(ItemElement):
            klass = Bill

            load_details = Link('.') & AsyncLoad

            obj_id = Format('%s_%d', Env('subid'), CleanDecimal(Env('id')))
            obj_format = 'pdf'
            obj_label = Format('Facture %d', CleanDecimal(Env('id')))
            obj_price = MyDecimal(Env('price'))

            def obj_url(self):
                return urljoin(self.page.url, Async('details', Link('.//a[contains(., "Reçu")]', default=NotAvailable))(self))

            def obj_date(self):
                return parse_french_date(CleanText('.//span[@class="history-col-date"]')(self)[:-6]).date()

            def obj_currency(self):
                return Bill.get_currency(CleanText(Env('price'))(self))

            def parse(self, el):
                self.env['id'] = Regexp(Link('.'), r'/orders/(.*)')(self)
                self.env['price'] = CleanText('.//span[@class="history-amount"]')(self)

            def condition(self):
                class_attr = Attr('.//span[has-class("history-col-status")]', 'class')(self)
                return not any([status in class_attr for status in ('failed', 'rejected', 'canceled')])
