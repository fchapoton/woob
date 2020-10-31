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

# flake8: compatible

from weboob.capabilities.bill import CapDocument, Subscription, Document, SubscriptionNotFound, DocumentNotFound
from weboob.capabilities.base import find_object, NotAvailable
from weboob.tools.backend import Module, BackendConfig
from weboob.tools.value import Value, ValueBackendPassword

from .browser import DeliverooBrowser


__all__ = ['DeliverooModule']


class DeliverooModule(Module, CapDocument):
    NAME = "deliveroo"
    DESCRIPTION = u"Deliveroo"
    MAINTAINER = u"Jean Walrave"
    EMAIL = u"jwalrave@budget-insight.com"
    LICENSE = 'LGPLv3+'
    VERSION = u"1.2"
    CONFIG = BackendConfig(
        Value('login', label='Adresse email'),
        ValueBackendPassword('password', label='Mot de passe'),
        Value('captcha_response', label='Reponse Captcha', required=False)
    )

    BROWSER = DeliverooBrowser

    def create_default_browser(self):
        return self.create_browser(self.config, self.config['login'].get(), self.config['password'].get())

    def iter_subscription(self):
        return self.browser.get_subscription_list()

    def get_subscription(self, _id):
        return find_object(self.iter_subscription(), id=_id, error=SubscriptionNotFound)

    def get_document(self, _id):
        subid = _id.rsplit('_', 1)[0]
        subscription = self.get_subscription(subid)

        return find_object(self.iter_documents(subscription), id=_id, error=DocumentNotFound)

    def iter_documents(self, subscription):
        if not isinstance(subscription, Subscription):
            subscription = self.get_subscription(subscription)
        return self.browser.iter_documents(subscription)

    def download_document(self, document):
        if not isinstance(document, Document):
            document = self.get_document(document)

        if document.url is NotAvailable:
            return

        return self.browser.open(document.url).content
