# -*- encoding: utf-8 -*-

# Copyright(C) 2020       Simon Bordeyne
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

from datetime import date

from woob.browser.pages import HTMLPage, LoggedPage, RawPage
from woob.browser.elements import ListElement, ItemElement, method
from woob.capabilities.bill import (
    Subscription, Document, DocumentTypes,
)
from woob.browser.filters.standard import (
    CleanText, Field, Format,
    Regexp, Date, Env, FilterError,
)
from woob.browser.filters.html import Attr, Link
from woob.tools.compat import urljoin


class BankStatementsPage(LoggedPage, HTMLPage):
    def submit_form(self, account_key):
        form = self.get_form(name='FiltersType')

        form['FiltersType[accountsKeys][]'] = account_key
        form['FiltersType[fromDate]'] = '01/01/1970'  # epoch, so we fetch as much as possible
        form['FiltersType[toDate]'] = date.today().strftime("%d/%m/%Y")
        form['FiltersType[documentsTypes][]'] = ['cc', 'export_historic_statement', 'cb', 'frais']

        return form.submit()

    @method
    class iter_subscriptions(ListElement):
        item_xpath = '//select[@id="FiltersType_accountsKeys"]//option'

        class item(ItemElement):
            klass = Subscription

            obj__account_key = Attr('.', 'value')
            obj_id = Regexp(CleanText('.'), r'([\d\*]+)')
            obj_subscriber = CleanText('//div[@id="dropdown-profile"]//div[has-class("user__username")]')

            def obj_label(self):
                _id = Field('id')(self)
                subscriber = Field('subscriber')(self)
                label = CleanText('.')(self)

                # label looks like: sequence1 - sequence2 - sequence3
                # but may contains more or less sequence
                values = label.split(' - ')
                position = values.index(_id)
                if position >= 0:
                    # obj_id is inside it, we remove it from label, since it's gotten in obj_id
                    values.pop(position)

                # and sometimes subscriber is inside, but can contains other text like: MR ...
                # or a - in subscriber (for some firstname), but not in label
                for idx, value in enumerate(values):
                    subscriber_values = subscriber.split()
                    # in subscriber it's in Title but in uppercase in label
                    if any(val.lower() in value.lower() for val in subscriber_values):
                        values.pop(idx)
                        break

                return ' - '.join(values)

    @method
    class iter_documents(ListElement):
        item_xpath = '//table/tbody/tr'

        def store(self, obj):
            # This code enables doc_id when there
            # are several docs with the exact same id
            # sometimes we have two docs on the same date
            # there is an id in the document url but it is
            # inconsistent
            _id = obj.id
            n = 1
            while _id in self.objects:
                n += 1
                _id = '%s-%s' % (obj.id, n)
            obj.id = _id
            self.objects[obj.id] = obj
            return obj

        class item(ItemElement):
            klass = Document

            obj_id = Format('%s_%s', Env('subid'), Field('date'))
            obj_type = DocumentTypes.STATEMENT
            obj_url = Link('.//td[2]/a')
            obj_label = CleanText('.//td[2]/a')

            def obj_format(self):
                if 'file-pdf' in Attr('.//td[1]/svg/use', 'xlink:href', default='')(self):
                    return 'pdf'

            def obj_date(self):
                try:
                    return Date(CleanText('.//td[4]'), dayfirst=True)(self)
                except FilterError:
                    # in some cases, there is no day (for example, with Relevés espèces for some action accounts)
                    # in this case, we return the first day of the given year and month
                    return Date(CleanText('.//td[4]'), strict=False)(self).replace(day=1)


class BankIdentityPage(LoggedPage, HTMLPage):
    @method
    class get_document(ListElement):
        item_xpath = '//table/tbody/tr'

        class item(ItemElement):
            klass = Document

            def condition(self):
                return Env('subid')(self) == Regexp(CleanText('.//td[1]/a'), r'(\d+)')(self)

            obj_id = Format('%s_RIB', Env('subid'))

            def obj_url(self):
                link = Link('.//td[1]/a')(self)
                return urljoin(self.page.url, urljoin(link, 'telecharger'))

            obj_format = CleanText('.//td[2]')
            obj_label = CleanText('.//td[1]/a')
            obj_type = DocumentTypes.RIB


class PdfDocumentPage(LoggedPage, RawPage):
    def is_here(self):
        return self.text.startswith('%PDF')
