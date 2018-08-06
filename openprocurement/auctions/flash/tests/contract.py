# -*- coding: utf-8 -*-
import unittest

from openprocurement.auctions.core.tests.base import snitch
from openprocurement.auctions.core.tests.contract import (
    AuctionContractResourceTestMixin,
    AuctionContractDocumentResourceTestMixin,
    Auction2LotContractDocumentResourceTestMixin
)
from openprocurement.auctions.core.tests.blanks.contract_blanks import (
    # Auction2LotContractResourceTest
    patch_auction_contract_2_lots,
)
from openprocurement.auctions.flash.tests.blanks.contract_blanks import (
    # AuctionContractResourceTest
    patch_auction_contract,
)
from openprocurement.auctions.core.plugins.contracting.v1.tests.contract import (
    AuctionContractV1ResourceTestCaseMixin
)

from openprocurement.auctions.flash.tests import fixtures
from openprocurement.auctions.flash.tests.base import (
    BaseAuctionWebTest,
    test_auction_data,
    test_bids,
    test_lots,
    test_organization
)


class AuctionContractResourceTest(
    BaseAuctionWebTest,
    AuctionContractResourceTestMixin,
    AuctionContractV1ResourceTestCaseMixin
):
    initial_status = 'active.auction'
    initial_bids = test_bids
    initial_organization = test_organization

    def setUp(self):
        super(AuctionContractResourceTest, self).setUp()
        # Create award
        fixtures.create_award(self)
        # Create contract for award
        self.app.patch_json('/auctions/{}/awards/{}?acc_token={}'.format(
            self.auction_id,
            self.award_id,
            self.auction_token
        ), {"data": {"status": "active"}}
        )
        response = self.app.get(
            '/auctions/{}/contracts'.format(
                self.auction_id
            )
        )
        self.contract = response.json['data'][0]
        self.contract_id = self.contract['id']

    test_patch_auction_contract = snitch(patch_auction_contract)


class Auction2LotContractResourceTest(BaseAuctionWebTest):
    initial_status = 'active.auction'
    initial_bids = test_bids
    initial_lots = 2 * test_lots

    def setUp(self):
        super(Auction2LotContractResourceTest, self).setUp()
        # Create award
        fixtures.create_award(self)
        # Create contract for award
        self.app.patch_json(
            '/auctions/{}/awards/{}?acc_token={}'.format(
                self.auction_id,
                self.award_id,
                self.auction_token
            ),
            {"data": {"status": "active"}})
        response = self.app.get(
            '/auctions/{}/contracts'.format(self.auction_id)
        )
        self.contract = response.json['data'][0]
        self.contract_id = self.contract['id']

    test_patch_auction_lots_contract = snitch(patch_auction_contract_2_lots)


class AuctionContractDocumentResourceTest(
        BaseAuctionWebTest,
        AuctionContractDocumentResourceTestMixin):
    initial_status = 'active.auction'
    initial_bids = test_bids
    docservice = True

    def setUp(self):
        super(AuctionContractDocumentResourceTest, self).setUp()
        # Create award
        fixtures.create_award( self)
        # Create contract for award
        self.app.patch_json('/auctions/{}/awards/{}?acc_token={}'.format(
            self.auction_id,
            self.award_id,
            self.auction_token
        ), {"data": {"status": "active"}})
        response = self.app.get(
            '/auctions/{}/contracts'.format(self.auction_id)
        )
        self.contract = response.json['data'][0]
        self.contract_id = self.contract['id']


class Auction2LotContractDocumentResourceTest(
        BaseAuctionWebTest,
        Auction2LotContractDocumentResourceTestMixin):
    initial_status = 'active.auction'
    initial_bids = test_bids
    initial_lots = 2 * test_lots

    def setUp(self):
        super(Auction2LotContractDocumentResourceTest, self).setUp()
        # Create award
        fixtures.create_award( self)
        # Create contract for award
        self.app.patch_json(
            '/auctions/{}/awards/{}?acc_token={}'.format(
                self.auction_id,
                self.award_id,
                self.auction_token
            ),
            {"data": {"status": "active"}}
        )
        response = self.app.get(
            '/auctions/{}/contracts'.format(self.auction_id)
        )
        self.contract = response.json['data'][0]
        self.contract_id = self.contract['id']


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(AuctionContractResourceTest))
    tests.addTest(unittest.makeSuite(Auction2LotContractResourceTest))
    tests.addTest(unittest.makeSuite(AuctionContractDocumentResourceTest))
    tests.addTest(unittest.makeSuite(Auction2LotContractDocumentResourceTest))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
