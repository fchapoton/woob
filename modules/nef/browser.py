# -*- coding: utf-8 -*-

# Copyright(C) 2019      Damien Cassou
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

import datetime

from woob.browser import LoginBrowser, URL, need_login
from woob.exceptions import BrowserIncorrectPassword

from .pages import LoginPage, HomePage, AccountsPage, RecipientsPage, TransactionsPage

def next_week_string():
    return (datetime.date.today() + datetime.timedelta(weeks=1)).strftime("%Y-%m-%d")

class NefBrowser(LoginBrowser):
    BASEURL = 'https://espace-client.lanef.com'

    home = URL('/templates/home.cfm', HomePage)
    main = URL('/templates/main.cfm', HomePage)
    download = URL(r'/templates/account/accountActivityListDownload.cfm\?viewMode=CSV&orderBy=TRANSACTION_DATE_DESCENDING&page=1&startDate=2016-01-01&endDate=%s&showBalance=true&AccNum=(?P<account_id>.*)' % next_week_string(), TransactionsPage)
    login = URL('/templates/logon/logon.cfm', LoginPage)

    def do_login(self):
        self.login.stay_or_go()

        self.page.login(self.username, self.password)

        if not self.home.is_here():
            raise BrowserIncorrectPassword('Error logging in')

    @need_login
    def iter_accounts_list(self):
        response = self.main.open(data={
            'templateName': 'account/accountList.cfm'
        })

        page = AccountsPage(self, response)
        return page.get_items()

    @need_login
    def iter_transactions_list(self, account):
        return self.download.go(account_id=account.id).iter_history()

    # CapBankTransfer
    @need_login
    def iter_recipients_list(self):
        response = self.main.open(data={
            'templateName': 'beneficiary/beneficiaryList.cfm',
            'LISTTYPE': 'HISTORY'
        })

        page = RecipientsPage(self, response)
        return page.get_items()
