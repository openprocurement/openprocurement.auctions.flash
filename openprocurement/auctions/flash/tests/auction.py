# -*- coding: utf-8 -*-
import unittest
from openprocurement.auctions.core.tests.base import snitch
from openprocurement.auctions.core.tests.auctions import (
    AuctionAuctionResourceTestMixin,
    AuctionLotAuctionResourceTestMixin,
)
from openprocurement.auctions.core.tests.blanks.auction_blanks import (
    post_auction_auction_not_changed,
    post_auction_auction_reversed,
    get_auction_features_auction,
)
from openprocurement.auctions.flash.tests.base import (
    BaseAuctionWebTest,
    test_features_auction_data,
    test_bids,
    test_lots,
    test_organization)

from openprocurement.auctions.flash.tests.blanks.auction_blanks import (
    post_auction_auction,
    # FlashAuctionBridgePeriodPatch
    set_auction_period,
    reset_auction_period
)


class AuctionAuctionResourceTest(
        BaseAuctionWebTest,
        AuctionAuctionResourceTestMixin):
    initial_status = 'active.tendering'
    initial_bids = test_bids
    test_post_auction_auction = snitch(post_auction_auction)


class AuctionSameValueAuctionResourceTest(BaseAuctionWebTest):
    initial_status = 'active.auction'
    initial_bids = [
        {
            "tenderers": [
                test_organization
            ],
            "value": {
                "amount": 469,
                "currency": "UAH",
                "valueAddedTaxIncluded": True
            }
        }
        for i in range(3)
    ]

    test_post_auction_auction_not_changed = snitch(
        post_auction_auction_not_changed)
    test_post_auction_auction_reversed = snitch(post_auction_auction_reversed)


class AuctionLotAuctionResourceTest(
        BaseAuctionWebTest,
        AuctionLotAuctionResourceTestMixin):
    initial_status = 'active.tendering'
    initial_bids = test_bids
    initial_lots = test_lots

    def test_get_auction_auction(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.get(
            '/auctions/{}/auction'.format(self.auction_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't get auction info in current (active.tendering) auction status")
        self.set_status('active.auction')
        response = self.app.get('/auctions/{}/auction'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        auction = response.json['data']
        self.assertNotEqual(auction, self.initial_data)
        self.assertIn('dateModified', auction)
        self.assertIn('minimalStep', auction)
        self.assertIn('lots', auction)
        self.assertNotIn("procuringEntity", auction)
        self.assertNotIn("tenderers", auction["bids"][0])
        self.assertEqual(
            auction["bids"][0]['lotValues'][0]['value']['amount'],
            self.initial_bids[0]['lotValues'][0]['value']['amount'])
        self.assertEqual(
            auction["bids"][1]['lotValues'][0]['value']['amount'],
            self.initial_bids[1]['lotValues'][0]['value']['amount'])

        self.set_status('active.qualification')

        response = self.app.get(
            '/auctions/{}/auction'.format(self.auction_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't get auction info in current (active.qualification) auction status")

    def test_post_auction_auction(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': {}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't report auction results in current (active.tendering) auction status")

        self.set_status('active.auction')

        response = self.app.post_json('/auctions/{}/auction'.format(self.auction_id), {
                                      'data': {'bids': [{'invalid_field': 'invalid_value'}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [{u'description': {
                         u'invalid_field': u'Rogue field'}, u'location': u'body', u'name': u'bids'}])

        patch_data = {
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    'lotValues': [
                        {
                            "value": {
                                "amount": 419,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": True
                            }
                        }
                    ]
                }
            ]
        }

        response = self.app.post_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Number of auction results did not match the number of auction bids")

        patch_data['bids'].append({
            'lotValues': [
                {
                    "value": {
                        "amount": 409,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": True
                    }
                }
            ]
        })

        patch_data['bids'][1]['id'] = "some_id"

        response = self.app.post_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], {
                         u'id': [u'Hash value is wrong length.']})

        patch_data['bids'][1]['id'] = "00000000000000000000000000000000"

        response = self.app.post_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Auction bids should be identical to the auction bids")

        patch_data['bids'][1]['id'] = self.initial_bids[0]['id']

        for lot in self.initial_lots:
            response = self.app.post_json(
                '/auctions/{}/auction/{}'.format(self.auction_id, lot['id']), {'data': patch_data})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            auction = response.json['data']

        self.assertNotEqual(
            auction["bids"][0]['lotValues'][0]['value']['amount'],
            self.initial_bids[0]['lotValues'][0]['value']['amount'])
        self.assertNotEqual(
            auction["bids"][1]['lotValues'][0]['value']['amount'],
            self.initial_bids[1]['lotValues'][0]['value']['amount'])
        self.assertEqual(
            auction["bids"][0]['lotValues'][0]['value']['amount'],
            patch_data["bids"][1]['lotValues'][0]['value']['amount'])
        self.assertEqual(
            auction["bids"][1]['lotValues'][0]['value']['amount'],
            patch_data["bids"][0]['lotValues'][0]['value']['amount'])
        self.assertEqual('active.qualification', auction["status"])
        self.assertIn("tenderers", auction["bids"][0])
        self.assertIn("name", auction["bids"][0]["tenderers"][0])
        # self.assertIn(auction["awards"][0]["id"], response.headers['Location'])
        self.assertEqual(
            auction["awards"][0]['bid_id'],
            patch_data["bids"][0]['id'])
        self.assertEqual(
            auction["awards"][0]['value']['amount'],
            patch_data["bids"][0]['lotValues'][0]['value']['amount'])
        self.assertEqual(
            auction["awards"][0]['suppliers'],
            self.initial_bids[0]['tenderers'])

        response = self.app.post_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't report auction results in current (active.qualification) auction status")

    def test_patch_auction_auction(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': {}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't update auction urls in current (active.tendering) auction status")

        self.set_status('active.auction')
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json(
            '/auctions/{}'.format(self.auction_id), {'data': {'id': self.auction_id}})
        self.assertEqual(response.status, '200 OK')

        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.patch_json('/auctions/{}/auction'.format(self.auction_id), {
                                       'data': {'bids': [{'invalid_field': 'invalid_value'}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [{u'description': {
                         u'invalid_field': u'Rogue field'}, u'location': u'body', u'name': u'bids'}])

        patch_data = {
            'auctionUrl': u'http://auction-sandbox.openprocurement.org/auctions/{}'.format(
                self.auction_id),
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    "participationUrl": u'http://auction-sandbox.openprocurement.org/auctions/{}?key_for_bid={}'.format(
                        self.auction_id,
                        self.initial_bids[1]['id'])}]}

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [{u'description': [{u'participationUrl': [
                         u'url should be posted for each lot of bid']}], u'location': u'body', u'name': u'bids'}])

        del patch_data['bids'][0]["participationUrl"]
        patch_data['bids'][0]['lotValues'] = [
            {
                "participationUrl": u'http://auction-sandbox.openprocurement.org/auctions/{}?key_for_bid={}'.format(
                    self.auction_id,
                    self.initial_bids[0]['id'])}]

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [{u'description': [
                         "url should be posted for each lot"], u'location': u'body', u'name': u'auctionUrl'}])

        patch_data['lots'] = [
            {
                "auctionUrl": patch_data.pop('auctionUrl')
            }
        ]

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Number of auction results did not match the number of auction bids")

        patch_data['bids'].append(
            {'lotValues': [
                {
                    "participationUrl":
                        u'http://auction-sandbox.openprocurement.org/auctions/{}?key_for_bid={}'.format(
                            self.auction_id,
                            self.initial_bids[0]['id']
                        )
                }
            ]}
        )

        patch_data['bids'][1]['id'] = "some_id"

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], {
                         u'id': [u'Hash value is wrong length.']})

        patch_data['bids'][1]['id'] = "00000000000000000000000000000000"

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Auction bids should be identical to the auction bids")

        patch_data['bids'][1]['id'] = self.initial_bids[0]['id']

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIsNone(response.json)

        for lot in self.initial_lots:
            response = self.app.patch_json(
                '/auctions/{}/auction/{}'.format(self.auction_id, lot['id']), {'data': patch_data})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            auction = response.json['data']

        self.assertEqual(
            auction["bids"][0]['lotValues'][0]['participationUrl'],
            patch_data["bids"][1]['lotValues'][0]['participationUrl'])
        self.assertEqual(
            auction["bids"][1]['lotValues'][0]['participationUrl'],
            patch_data["bids"][0]['lotValues'][0]['participationUrl'])
        self.assertEqual(
            auction["lots"][0]['auctionUrl'],
            patch_data["lots"][0]['auctionUrl'])

        self.set_status('complete')

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't update auction urls in current (complete) auction status")

    def test_post_auction_auction_document(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post(
            '/auctions/{}/documents'.format(
                self.auction_id), upload_files=[
                ('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't add document in current (active.tendering) auction status")

        self.set_status('active.auction')

        response = self.app.post(
            '/auctions/{}/documents'.format(
                self.auction_id), upload_files=[
                ('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        response = self.app.patch_json(
            '/auctions/{}/documents/{}'.format(
                self.auction_id, doc_id), {
                'data': {
                    "documentOf": "lot", 'relatedItem': self.initial_lots[0]['id']}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"]["documentOf"], "lot")
        self.assertEqual(
            response.json["data"]["relatedItem"],
            self.initial_lots[0]['id'])

        patch_data = {
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    'lotValues': [
                        {
                            "value": {
                                "amount": 409,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": True
                            }
                        }
                    ]
                },
                {
                    'id': self.initial_bids[0]['id'],
                    'lotValues': [
                        {
                            "value": {
                                "amount": 419,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": True
                            }
                        }
                    ]
                }
            ]
        }

        response = self.app.post_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.put(
            '/auctions/{}/documents/{}'.format(
                self.auction_id, doc_id), upload_files=[
                ('file', 'name.doc', 'content_with_names')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key2 = response.json["data"]["url"].split('?')[-1].split('=')[-1]
        self.assertNotEqual(key, key2)

        self.set_status('complete')
        response = self.app.post(
            '/auctions/{}/documents'.format(
                self.auction_id), upload_files=[
                ('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't add document in current (complete) auction status")


class AuctionMultipleLotAuctionResourceTest(AuctionAuctionResourceTest):
    initial_lots = 2 * test_lots

    def test_get_auction_auction(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.get(
            '/auctions/{}/auction'.format(self.auction_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't get auction info in current (active.tendering) auction status")

        self.set_status('active.auction')

        response = self.app.get('/auctions/{}/auction'.format(self.auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        auction = response.json['data']
        self.assertNotEqual(auction, self.initial_data)
        self.assertIn('dateModified', auction)
        self.assertIn('minimalStep', auction)
        self.assertIn('lots', auction)
        self.assertNotIn("procuringEntity", auction)
        self.assertNotIn("tenderers", auction["bids"][0])
        self.assertEqual(
            auction["bids"][0]['lotValues'][0]['value']['amount'],
            self.initial_bids[0]['lotValues'][0]['value']['amount'])
        self.assertEqual(
            auction["bids"][1]['lotValues'][0]['value']['amount'],
            self.initial_bids[1]['lotValues'][0]['value']['amount'])
        self.assertEqual(
            auction["bids"][0]['lotValues'][1]['value']['amount'],
            self.initial_bids[0]['lotValues'][1]['value']['amount'])
        self.assertEqual(
            auction["bids"][1]['lotValues'][1]['value']['amount'],
            self.initial_bids[1]['lotValues'][1]['value']['amount'])

        self.set_status('active.qualification')

        response = self.app.get(
            '/auctions/{}/auction'.format(self.auction_id), status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't get auction info in current (active.qualification) auction status")

    def test_post_auction_auction(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': {}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't report auction results in current (active.tendering) auction status")

        self.set_status('active.auction')

        response = self.app.post_json('/auctions/{}/auction'.format(self.auction_id), {
                                      'data': {'bids': [{'invalid_field': 'invalid_value'}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [{u'description': {
                         u'invalid_field': u'Rogue field'}, u'location': u'body', u'name': u'bids'}])

        patch_data = {
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    'lotValues': [
                        {
                            "value": {
                                "amount": 419,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": True
                            }
                        }
                    ]
                }
            ]
        }

        response = self.app.post_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Number of auction results did not match the number of auction bids")

        patch_data['bids'].append({
            'lotValues': [
                {
                    "value": {
                        "amount": 409,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": True
                    }
                }
            ]
        })

        patch_data['bids'][1]['id'] = "some_id"

        response = self.app.post_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], {
                         u'id': [u'Hash value is wrong length.']})

        patch_data['bids'][1]['id'] = "00000000000000000000000000000000"

        response = self.app.post_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Auction bids should be identical to the auction bids")

        patch_data['bids'][1]['id'] = self.initial_bids[0]['id']

        response = self.app.post_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], [{"lotValues": [
                         "Number of lots of auction results did not match the number of auction lots"]}])

        for bid in patch_data['bids']:
            bid['lotValues'] = [bid['lotValues'][0].copy()
                                for i in self.initial_lots]

        patch_data['bids'][0]['lotValues'][1]['relatedLot'] = self.initial_bids[0]['lotValues'][0]['relatedLot']

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], [{u'lotValues': [
                         {u'relatedLot': [u'relatedLot should be one of lots of bid']}]}])

        patch_data['bids'][0]['lotValues'][1]['relatedLot'] = self.initial_bids[0]['lotValues'][1]['relatedLot']

        for lot in self.initial_lots:
            response = self.app.post_json(
                '/auctions/{}/auction/{}'.format(self.auction_id, lot['id']), {'data': patch_data})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            auction = response.json['data']

        self.assertNotEqual(
            auction["bids"][0]['lotValues'][0]['value']['amount'],
            self.initial_bids[0]['lotValues'][0]['value']['amount'])
        self.assertNotEqual(
            auction["bids"][1]['lotValues'][0]['value']['amount'],
            self.initial_bids[1]['lotValues'][0]['value']['amount'])
        self.assertEqual(
            auction["bids"][0]['lotValues'][0]['value']['amount'],
            patch_data["bids"][1]['lotValues'][0]['value']['amount'])
        self.assertEqual(
            auction["bids"][1]['lotValues'][0]['value']['amount'],
            patch_data["bids"][0]['lotValues'][0]['value']['amount'])
        self.assertEqual('active.qualification', auction["status"])
        self.assertIn("tenderers", auction["bids"][0])
        self.assertIn("name", auction["bids"][0]["tenderers"][0])
        # self.assertIn(auction["awards"][0]["id"], response.headers['Location'])
        self.assertEqual(
            auction["awards"][0]['bid_id'],
            patch_data["bids"][0]['id'])
        self.assertEqual(
            auction["awards"][0]['value']['amount'],
            patch_data["bids"][0]['lotValues'][0]['value']['amount'])
        self.assertEqual(
            auction["awards"][0]['suppliers'],
            self.initial_bids[0]['tenderers'])

        response = self.app.post_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't report auction results in current (active.qualification) auction status")

    def test_patch_auction_auction(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': {}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't update auction urls in current (active.tendering) auction status")

        self.set_status('active.auction')
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json(
            '/auctions/{}'.format(self.auction_id), {'data': {'id': self.auction_id}})
        self.assertEqual(response.status, '200 OK')

        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.patch_json('/auctions/{}/auction'.format(self.auction_id), {
                                       'data': {'bids': [{'invalid_field': 'invalid_value'}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [{u'description': {
                         u'invalid_field': u'Rogue field'}, u'location': u'body', u'name': u'bids'}])

        patch_data = {
            'auctionUrl': u'http://auction-sandbox.openprocurement.org/auctions/{}'.format(
                self.auction_id),
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    "participationUrl": u'http://auction-sandbox.openprocurement.org/auctions/{}?key_for_bid={}'.format(
                        self.auction_id,
                        self.initial_bids[1]['id'])}]}

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [{u'description': [{u'participationUrl': [
                         u'url should be posted for each lot of bid']}], u'location': u'body', u'name': u'bids'}])

        del patch_data['bids'][0]["participationUrl"]
        patch_data['bids'][0]['lotValues'] = [
            {
                "participationUrl": u'http://auction-sandbox.openprocurement.org/auctions/{}?key_for_bid={}'.format(
                    self.auction_id,
                    self.initial_bids[0]['id'])}]

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [{u'description': [
                         "url should be posted for each lot"], u'location': u'body', u'name': u'auctionUrl'}])

        patch_data['lots'] = [
            {
                "auctionUrl": patch_data.pop('auctionUrl')
            }
        ]

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Number of auction results did not match the number of auction bids")

        patch_data['bids'].append(
            {
                'lotValues': [
                    {
                        "participationUrl":
                            u'http://auction-sandbox.openprocurement.org/auctions/{}?key_for_bid={}'.format(
                                self.auction_id,
                                self.initial_bids[0]['id'])}]})

        patch_data['bids'][1]['id'] = "some_id"

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], {
                         u'id': [u'Hash value is wrong length.']})

        patch_data['bids'][1]['id'] = "00000000000000000000000000000000"

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Auction bids should be identical to the auction bids")

        patch_data['bids'][1]['id'] = self.initial_bids[0]['id']

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            u'Number of lots did not match the number of auction lots')

        patch_data['lots'] = [patch_data['lots'][0].copy()
                              for i in self.initial_lots]
        patch_data['lots'][1]['id'] = "00000000000000000000000000000000"

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            u'Auction lots should be identical to the auction lots')

        patch_data['lots'][1]['id'] = self.initial_lots[1]['id']

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], [{"lotValues": [
                         "Number of lots of auction results did not match the number of auction lots"]}])

        for bid in patch_data['bids']:
            bid['lotValues'] = [bid['lotValues'][0].copy()
                                for i in self.initial_lots]

        patch_data['bids'][0]['lotValues'][1]['relatedLot'] = self.initial_bids[0]['lotValues'][0]['relatedLot']

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], [{u'lotValues': [
                         {u'relatedLot': [u'relatedLot should be one of lots of bid']}]}])

        patch_data['bids'][0]['lotValues'][1]['relatedLot'] = self.initial_bids[0]['lotValues'][1]['relatedLot']

        response = self.app.patch_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIsNone(response.json)

        for lot in self.initial_lots:
            response = self.app.patch_json(
                '/auctions/{}/auction/{}'.format(self.auction_id, lot['id']), {'data': patch_data}
            )
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            auction = response.json['data']

        self.assertEqual(
            auction["bids"][0]['lotValues'][0]['participationUrl'],
            patch_data["bids"][1]['lotValues'][0]['participationUrl'])
        self.assertEqual(
            auction["bids"][1]['lotValues'][0]['participationUrl'],
            patch_data["bids"][0]['lotValues'][0]['participationUrl'])
        self.assertEqual(
            auction["lots"][0]['auctionUrl'],
            patch_data["lots"][0]['auctionUrl'])

        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json(
            '/auctions/{}/cancellations?acc_token={}'.format(
                self.auction_id, self.auction_token
            ), {'data': {'reason': 'cancellation reason',
                         'status': 'active',
                         'cancellationOf': 'lot',
                         'relatedLot': self.initial_lots[0]['id']}
                }
        )
        self.assertEqual(response.status, '201 Created')

        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.patch_json(
            '/auctions/{}/auction/{}'.format(
                self.auction_id, self.initial_lots[0]['id']), {
                'data': patch_data}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can update auction urls only in active lot status")

    def test_post_auction_auction_document(self):
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post(
            '/auctions/{}/documents'.format(
                self.auction_id), upload_files=[
                ('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't add document in current (active.tendering) auction status")

        self.set_status('active.auction')

        response = self.app.post(
            '/auctions/{}/documents'.format(
                self.auction_id), upload_files=[
                ('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        key = response.json["data"]["url"].split('?')[-1].split('=')[-1]

        response = self.app.patch_json(
            '/auctions/{}/documents/{}'.format(
                self.auction_id, doc_id), {
                'data': {
                    "documentOf": "lot", 'relatedItem': self.initial_lots[0]['id']}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"]["documentOf"], "lot")
        self.assertEqual(
            response.json["data"]["relatedItem"],
            self.initial_lots[0]['id'])

        patch_data = {
            'bids': [
                {
                    "id": self.initial_bids[1]['id'],
                    'lotValues': [
                        {
                            "value": {
                                "amount": 409,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": True
                            }
                        }
                        for i in self.initial_lots
                    ]
                },
                {
                    'id': self.initial_bids[0]['id'],
                    'lotValues': [
                        {
                            "value": {
                                "amount": 419,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": True
                            }
                        }
                        for i in self.initial_lots
                    ]
                }
            ]
        }

        response = self.app.post_json(
            '/auctions/{}/auction'.format(self.auction_id), {'data': patch_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.put(
            '/auctions/{}/documents/{}'.format(
                self.auction_id, doc_id), upload_files=[
                ('file', 'name.doc', 'content_with_names')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key2 = response.json["data"]["url"].split('?')[-1].split('=')[-1]
        self.assertNotEqual(key, key2)

        self.set_status('complete')
        response = self.app.post(
            '/auctions/{}/documents'.format(
                self.auction_id), upload_files=[
                ('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['errors'][0]["description"],
            "Can't add document in current (complete) auction status")


class AuctionFeaturesAuctionResourceTest(BaseAuctionWebTest):
    initial_data = test_features_auction_data
    initial_status = 'active.auction'
    initial_bids = [
        {
            "parameters": [
                {
                    "code": i["code"],
                    "value": 0.1,
                }
                for i in test_features_auction_data['features']
            ],
            "tenderers": [
                test_organization
            ],
            "value": {
                "amount": 469,
                "currency": "UAH",
                "valueAddedTaxIncluded": True
            }
        },
        {
            "parameters": [
                {
                    "code": i["code"],
                    "value": 0.15,
                }
                for i in test_features_auction_data['features']
            ],
            "tenderers": [
                test_organization
            ],
            "value": {
                "amount": 479,
                "currency": "UAH",
                "valueAddedTaxIncluded": True
            }
        }
    ]
    test_get_auction_auction = snitch(get_auction_features_auction)


class FlashAuctionBridgePeriodPatchTest(BaseAuctionWebTest):
    initial_bids = test_bids
    test_set_auction_period = snitch(set_auction_period)
    test_reset_auction_period = snitch(reset_auction_period)


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(AuctionAuctionResourceTest))
    tests.addTest(unittest.makeSuite(AuctionSameValueAuctionResourceTest))
    tests.addTest(unittest.makeSuite(AuctionLotAuctionResourceTest))
    tests.addTest(unittest.makeSuite(AuctionMultipleLotAuctionResourceTest))
    tests.addTest(unittest.makeSuite(AuctionFeaturesAuctionResourceTest))
    tests.addTest(unittest.makeSuite(FlashAuctionBridgePeriodPatchTest))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
