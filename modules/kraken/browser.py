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


import hashlib
import hmac
import base64
import time

from weboob.browser import PagesBrowser, URL, StatesMixin, need_login
from weboob.tools.compat import urlencode
from weboob.exceptions import (
    BrowserIncorrectPassword, NocaptchaQuestion, BrowserUnavailable,
)
from .pages import (
    BalancePage, HistoryPage, LoginPage, APISettingsPage,
    AjaxPage, AssetsPage, AssetPairsPage, TickerPage,
)


class KrakenBrowser(PagesBrowser, StatesMixin):
    BASEURL = 'https://api.kraken.com'

    login = URL('https://www.kraken.com/login', LoginPage)
    apisettting = URL('https://www.kraken.com/u/settings/api', APISettingsPage)
    ajaxpage = URL('https://www.kraken.com/ajax', AjaxPage)

    balance = URL('/0/private/Balance', BalancePage)
    history = URL('/0/private/Ledgers', HistoryPage)

    assets = URL('/0/public/Assets', AssetsPage)
    assetpairs = URL('/0/public/AssetPairs', AssetPairsPage)
    ticker = URL('/0/public/Ticker\?pair=(?P<asset_pair>.*)', TickerPage)

    api_key = None
    private_key = None

    __states__ = ('api_key', 'private_key')

    def __init__(self, config, *args, **kwargs):
        self.config = config
        super(KrakenBrowser, self).__init__(*args, **kwargs)

        self.token = None
        self.data = {}
        self.headers = {}
        self.accounts_list = []
        self.asset_pair_list = []

    def locate_browser(self, state):
        pass

    def do_login(self):
        if self.config['captcha_response'].get():
            self.do_weblogin()

        # create a new API key on the website, or get the details of an existing key, if no data in the StatesMixin
        if not self.api_key:
            if not self.token:
                self.do_weblogin()

            if self.config['key_name'].get() in self.get_api_key_list():
                (self.api_key, self.private_key) = self.get_api_key_details()
            else:
                (self.api_key, self.private_key) = self.create_api_key()

        # check if the key-pairs work well, recreate it in case of error
        if not self.api_key_is_ok():
            if not self.token:
                self.do_weblogin()

            # delete and recreate the key if exists on the website, but not working
            if self.config['key_name'].get() in self.get_api_key_list():
                self.delete_api_key()
            (self.api_key, self.private_key) = self.create_api_key()
        else:
            self.accounts_list = self.page.iter_accounts()

    def api_key_is_ok(self):
        self.update_request_data()
        self.update_request_headers('Balance')
        # return if it works
        try:
            self.balance.go(data=self.data, headers=self.headers)
        except BrowserUnavailable:
            return False
        return True

    #############################
    # Navigation on the website #
    # to change API key configs #
    #############################

    def do_weblogin(self):
        if not self.config['captcha_response'].get():
            # clear cookies to be sure to arrive to the good login page
            self.session.cookies.clear()
            self.login.go()

        # sometimes we have a reCaptcha
        if self.page.has_captcha():
            self.do_weblogin_with_captcha()
        else:
            self.page.login(self.config['username'].get(), self.config['password'].get(), self.config['otp'].get())
            # sometimes when we have no captcha at the first time, we are redirected to the login page with captcha
            if self.login.is_here() and self.page.has_captcha():
                self.do_weblogin_with_captcha()

        if self.login.is_here():
            raise BrowserIncorrectPassword(self.page.get_error())

        # go to the settings page
        self.apisettting.go()
        self.session.headers.update({"X-Requested-With": "XMLHttpRequest"})
        self.token = self.page.get_token()

    def do_weblogin_with_captcha(self):
        if not self.config['captcha_response'].get():
            website_url = self.url
            website_key = self.page.get_captcha_key()
            raise NocaptchaQuestion(website_key=website_key, website_url=website_url)
        else:
            self.page.login(self.config['username'].get(), self.config['password'].get(), self.config['otp'].get(), captcha_response=self.config['captcha_response'].get())

    def get_api_key_list(self):
        data = {'a': 'api',
                'x': 'list',
                'csrftoken': self.token
                }
        (keylist, self.token) = self.ajaxpage.go(data=data).get_keylist()
        return [x['descr'] for x in keylist]

    def delete_api_key(self):
        data = {'a': 'api',
                'x': 'delete',
                'csrftoken': self.token,
                'description': self.config['key_name'].get()
                }
        self.token = self.ajaxpage.go(data=data).get_new_token()

    def get_api_key_details(self):
        data = {'a': 'api',
                'x': 'get',
                'csrftoken': self.token,
                'description': self.config['key_name'].get()
                }
        self.token = self.ajaxpage.go(data=data).get_new_token()
        return self.page.get_key_details()

    def create_api_key(self):
        data = [('a', 'api'),
                ('x', 'generate'),
                ('csrftoken', self.token),
                ('keydescription', ''),
                ('description', self.config['key_name'].get()),
                ('keydescription', '0'),
                ('permissions[]', 'funds-query'),
                ('permissions[]', 'funds-add'),
                ('permissions[]', 'funds-withdraw'),
                ('permissions[]', 'trades-query-open'),
                ('permissions[]', 'trades-query-closed'),
                ('permissions[]', 'trades-modify'),
                ('permissions[]', 'trades-close'),
                ('permissions[]', 'ledger-query'),
                ('permissions[]', 'export-data'),
                ('validuntil', '0'),
                ('queryfrom', '0'),
                ('queryto', '0')
                ]
        self.token = self.ajaxpage.go(data=data).get_new_token()
        return self.page.get_new_key_details()


    ##############################
    # Communication with the API #
    ##############################

    def _sign(self, data, urlpath):
        # sign request data according to Kraken's scheme.
        postdata = urlencode(data)

        # unicode-objects must be encoded before hashing
        encoded = (str(data['nonce']) + postdata).encode(encoding="ascii")
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        signature = hmac.new(base64.b64decode(self.private_key),
                             message, hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest())

        return sigdigest.decode(encoding="ascii")

    def update_request_headers(self, method):
        urlpath = '/0/private/' + method
        self.headers = {
            'API-Key': self.api_key,
            'API-Sign': self._sign(self.data, urlpath)
        }

    def update_request_data(self):
        # nonce counter: returns: an always-increasing unsigned integer (up to 64 bits wide)
        self.data['nonce'] = int(1000*time.time())

    @need_login
    def iter_accounts(self):
        if self.accounts_list:
            return self.accounts_list
        self.update_request_data()
        self.update_request_headers('Balance')
        self.balance.go(data=self.data, headers=self.headers)

        return self.page.iter_accounts()

    @need_login
    def iter_history(self, account_currency):
        self.update_request_data()
        self.update_request_headers('Ledgers')
        self.history.go(data=self.data, headers=self.headers)

        return self.page.get_tradehistory(account_currency)

    def iter_currencies(self):
        return self.assets.go().iter_currencies()

    def get_rate(self, curr_from, curr_to):
        if not self.asset_pair_list:
            self.asset_pair_list = self.assetpairs.go().get_asset_pairs()

        # search the correct asset pair name
        for asset_pair in self.asset_pair_list:
            if (curr_from in asset_pair) and (curr_to in asset_pair):
                rate = self.ticker.go(asset_pair=asset_pair).get_rate()
                # in kraken API curreny_from must be the crypto in the spot price request
                if asset_pair.find(curr_from) > asset_pair.find(curr_to):
                    rate.value = 1 / rate.value
                return rate
        return
