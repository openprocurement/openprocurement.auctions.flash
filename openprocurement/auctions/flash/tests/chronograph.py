# -*- coding: utf-8 -*-
import unittest

from openprocurement.auctions.core.tests.base import snitch

from openprocurement.auctions.core.tests.blanks.chronograph_blanks import (
    # AuctionSwitchAuctionResourceTest
    switch_to_auction,
    # AuctionSwitchUnsuccessfulResourceTest
    switch_to_unsuccessful,
    # AuctionComplaintSwitchResourceTest
    switch_to_pending,
    switch_to_complaint,
    # AuctionAwardComplaintSwitchResourceTest
    switch_to_pending_award,
    switch_to_complaint_award,
)

from openprocurement.auctions.flash.tests import fixtures
from openprocurement.auctions.flash.tests.base import (
    BaseAuctionWebTest, test_lots, test_bids, test_organization
)
from openprocurement.auctions.flash.tests.blanks.chronograph_blanks import (
    # AuctionSwitchtenderingResourceTest
    switch_to_tendering_by_enquiryPeriod_endDate,
    switch_to_tendering_by_auctionPeriod_startDate,
    switch_to_tendering_auctionPeriod,
    # AuctionSwitchQualificationResourceTest
    switch_to_qualification,
)


class AuctionSwitchtenderingResourceTest(BaseAuctionWebTest):
    test_switch_to_tendering_by_enquiryPeriod_endDate = \
        snitch(switch_to_tendering_by_enquiryPeriod_endDate)
    test_switch_to_tendering_by_auctionPeriod_startDate = \
        snitch(switch_to_tendering_by_auctionPeriod_startDate)
    test_switch_to_tendering_auctionPeriod = \
        snitch(switch_to_tendering_auctionPeriod)


class AuctionSwitchQualificationResourceTest(BaseAuctionWebTest):
    initial_status = 'active.tendering'
    initial_bids = test_bids[:1]
    test_switch_to_qualification = snitch(switch_to_qualification)


class AuctionSwitchAuctionResourceTest(BaseAuctionWebTest):
    initial_status = 'active.tendering'
    initial_bids = test_bids
    test_switch_to_auction = snitch(switch_to_auction)


class AuctionSwitchUnsuccessfulResourceTest(BaseAuctionWebTest):
    initial_status = 'active.tendering'
    test_switch_to_unsuccessful = snitch(switch_to_unsuccessful)


class AuctionLotSwitchQualificationResourceTest(
    AuctionSwitchQualificationResourceTest
):
    initial_lots = test_lots


class AuctionLotSwitchAuctionResourceTest(AuctionSwitchAuctionResourceTest):
    initial_lots = test_lots


class AuctionLotSwitchUnsuccessfulResourceTest(
    AuctionSwitchUnsuccessfulResourceTest
):
    initial_lots = test_lots


class AuctionComplaintSwitchResourceTest(BaseAuctionWebTest):
    initial_organization = test_organization

    test_switch_to_pending = snitch(switch_to_pending)
    test_switch_to_complaint = snitch(switch_to_complaint)


class AuctionLotComplaintSwitchResourceTest(
    AuctionComplaintSwitchResourceTest
):
    initial_lots = test_lots


class AuctionAwardComplaintSwitchResourceTest(BaseAuctionWebTest):
    initial_status = 'active.auction'
    initial_bids = test_bids
    initial_organization = test_organization

    def setUp(self):
        super(AuctionAwardComplaintSwitchResourceTest, self).setUp()
        # Create award
        fixtures.create_award(self)

    test_auction_award_complaint_switch_to_pending = snitch(
        switch_to_pending_award
    )
    test_auction_award_complaint_switch_to_complaint = snitch(
        switch_to_complaint_award
    )


class AuctionLotAwardComplaintSwitchResourceTest(
    AuctionAwardComplaintSwitchResourceTest
):
    initial_status = 'active.auction'
    initial_lots = test_lots

    def setUp(self):
        super(AuctionAwardComplaintSwitchResourceTest, self).setUp()
        # Create award
        fixtures.create_award(self)


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(AuctionSwitchtenderingResourceTest))
    tests.addTest(unittest.makeSuite(AuctionSwitchQualificationResourceTest))
    tests.addTest(unittest.makeSuite(AuctionSwitchAuctionResourceTest))
    tests.addTest(unittest.makeSuite(AuctionSwitchUnsuccessfulResourceTest))
    tests.addTest(unittest.makeSuite(
        AuctionLotSwitchQualificationResourceTest
    ))
    tests.addTest(unittest.makeSuite(AuctionLotSwitchAuctionResourceTest))
    tests.addTest(unittest.makeSuite(AuctionLotSwitchUnsuccessfulResourceTest))
    tests.addTest(unittest.makeSuite(AuctionComplaintSwitchResourceTest))
    tests.addTest(unittest.makeSuite(AuctionLotComplaintSwitchResourceTest))
    tests.addTest(unittest.makeSuite(AuctionAwardComplaintSwitchResourceTest))
    tests.addTest(unittest.makeSuite(
        AuctionLotAwardComplaintSwitchResourceTest
    ))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
