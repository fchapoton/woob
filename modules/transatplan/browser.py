# -*- coding: utf-8 -*-

# Copyright(C) 2012-2021  Budget Insight
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

# flake8: compatible

from __future__ import unicode_literals

from decimal import Decimal

from woob.capabilities.bank import Account
from woob.capabilities.wealth import Investment
from woob.browser import LoginBrowser, need_login, URL
from woob.exceptions import BrowserIncorrectPassword, NoAccountsException, ActionNeeded
from woob.tools.capabilities.bank.investments import IsinType

from .pages import (
    LoginPage, HomePage, HistoryPage, AccountPage, ErrorPage,
    InvestmentDetailPage, InvestmentPerformancePage, SituationPage,
    PocketsPage, PocketDetailPage, ActionNeededPage,
)


class TransatplanBrowser(LoginBrowser):
    BASEURL = 'https://transatplan.banquetransatlantique.com'

    error = URL(r'.*', ErrorPage)
    login = URL(r'/fr/identification/authentification.html', LoginPage)
    action_needed = URL(r'/fr/client/votre-situation.aspx\?FID=GoOngletCompte', ActionNeededPage)
    situation = URL(r'/fr/client/votre-situation.aspx$', SituationPage)
    account = URL(
        r'/fr/client/votre-situation.aspx\?FID=GoOngletCompte',
        r'/fr/client/votre-situation.aspx\?.*GoRetour.*',
        r'/fr/client/votre-situation.aspx\?.*GoCourLst.*',
        AccountPage
    )
    investment_detail = URL(r'/fr/client/votre-situation.aspx\?.*GoCourLst.*', InvestmentDetailPage)
    investment_performance = URL(r'/fr/client/VAL_FicheCours.aspx.*', InvestmentPerformancePage)
    pockets = URL(
        r'/fr/client/votre-situation.aspx\?FID=GoSituation',
        r'/fr/client/votre-situation.aspx\?_productfilter=',
        PocketsPage
    )
    history = URL(r'/fr/client/votre-situation.aspx\?_productfilter=.*GoCptMvt.*', HistoryPage)
    pocket_details = URL(r'/fr/client/votre-situation.aspx\?_productfilter=', PocketDetailPage)
    home = URL(r'/fr/client/Accueil.aspx\?FID=GoSitAccueil.*', HomePage)

    def do_login(self):
        self.login.go()
        self.page.login(self.username, self.password)
        if self.login.is_here():
            raise BrowserIncorrectPassword(self.page.get_error())
        if self.situation.is_here() or self.action_needed.is_here():
            raise ActionNeeded(self.page.get_action_needed())
        assert self.page

    @need_login
    def iter_accounts(self):
        self.account.stay_or_go()

        if self.page.has_no_account():
            raise NoAccountsException()

        for account in self.page.iter_especes():
            checking_id = account.id
            yield account

        company_name = self.page.get_company_name()
        # if there is no market account, we need to create one
        if self.page.has_no_market_account():
            self.pockets.go()
            # check if pockets exists in PocketsPage
            if self.page.has_pockets():
                yield self.create_market_account(checking_id, company_name)
        else:
            for account in self.page.iter_titres():
                account.company_name = company_name
                yield account

    @need_login
    def iter_history(self, account):
        # The website does not know what is a history
        if not account.url or account.type == Account.TYPE_MARKET:
            return []

        self.location(account.url)
        history = self.page.iter_history()

        self.do_return()

        return history

    @need_login
    def iter_investment(self, account):
        if account.type != Account.TYPE_MARKET:
            return

        self.account.go()
        if self.page.has_no_market_account():
            yield self.create_invest_from_pocket()
        else:
            investments = self.page.iter_investment()
            for inv in investments:
                if inv._performance_url:
                    self.location(inv._performance_url)
                    link = self.page.get_performance_link()
                    self.page.fill_investment(obj=inv)
                    if link:
                        self.location(link)
                        self.page.fill_investment(obj=inv)
                yield inv

        self.do_return()

    @need_login
    def iter_pocket(self, account):
        if account.type != Account.TYPE_MARKET:
            return

        for inv in self.iter_investment(account):
            self.pockets.go()
            for pocket in self.page.iter_pocket(inv=inv):
                # we need to navigate to the details page of each pocket.
                # to do so, we must retrieve the link for each pocket one by one,
                # because there is a "_state" parameter in the link that is generated
                # everytime we change page, and it's unique.
                # if we fetch all the link at the same time in iter_pocket, only
                # the first link will be valid and we would be stuck on the same page.
                # if we cannot find '_url_id', we ignore the pocket.
                if pocket._url_id:
                    # we go to the pocket details page
                    self.location(self.page.get_detail_url(pocket._url_id))
                    self.page.fill_pocket(obj=pocket)
                    back_link = self.page.get_back_url()
                    # we go back to PocketPage by using the "Retour" button link.
                    # in case the link cannot be retrieved, we go back to PocketsPage
                    # both request will lead us to PocketsPage.
                    if back_link:
                        self.location(back_link)
                    else:
                        self.pockets.go()
                    yield pocket

    def do_return(self):
        if hasattr(self.page, 'do_return'):
            self.page.do_return()

    def create_market_account(self, checking_id, company_name):
        acc = Account()

        # create the new future ID of the market account.
        # based on connections with a market account,
        # the id of the market account is always checking account + 1.
        acc.id = str(int(checking_id) + 1).zfill(11)
        acc.type = Account.TYPE_MARKET
        acc.company_name = company_name
        # we must go through all the pocket navigation to fill the information of the account
        self.pockets.go()
        acc.balance = self.page.get_valuation()
        acc.currency = self.page.get_currency()
        # we go to PocketDetailPage
        self.location(self.page.get_pocket_details_link())
        # we go to InvestmentDetailPage
        self.location(self.page.get_invest_url())
        # we go to InvestmentPerformancePage
        self.location(self.page.get_performance_link())
        # we mimic the exact future name of the market account that will be displayed
        # when the first pocket will be acquired.
        acc.label = "Plan d'attributions d'actions %s" % self.page.get_invest_label()

        return acc

    def create_invest_from_pocket(self):
        inv = Investment()
        inv.quantity = Decimal(0)
        inv.portfolio_share = Decimal(1)
        self.pockets.go()
        inv.valuation = self.page.get_valuation()
        # we must iter through all the non_acquired pockets
        # to get the total quantity of the pockets
        for pocket in self.page.iter_pocket():
            inv.quantity += pocket.quantity

        # we must go through all the pocket navigation to fill the information of the invest
        # we go to PocketDetailPage
        self.location(self.page.get_pocket_details_link())
        inv.code = self.page.get_invest_isin()
        inv.code_type = IsinType().filter(inv.code)
        # we go to InvestmentDetailPage
        self.location(self.page.get_invest_url())
        self.page.fill_investment(obj=inv)
        # we go to InvestmentPerformancePage
        self.location(self.page.get_performance_link())
        inv.label = self.page.get_invest_label()
        self.page.fill_investment(obj=inv)

        return inv
