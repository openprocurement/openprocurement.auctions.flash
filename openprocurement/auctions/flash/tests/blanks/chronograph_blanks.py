# -*- coding: utf-8 -*-

# AuctionSwitchtenderingResourceTest


def switch_to_tendering_by_enquiryPeriod_endDate(self):
    self.app.authorization = ('Basic', ('chronograph', ''))
    response = self.app.patch_json(
        '/auctions/{}'.format(self.auction_id), {'data': {'id': self.auction_id}})
    self.assertEqual(response.status, '200 OK')
    date_1 = response.json['data']['date']
    self.assertNotEqual(response.json['data']["status"], "active.tendering")
    self.set_status(
        'active.tendering', {
            'status': 'active.enquiries', "tenderPeriod": {
                "startDate": None}})
    response = self.app.patch_json(
        '/auctions/{}'.format(self.auction_id), {'data': {'id': self.auction_id}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']["status"], "active.tendering")
    self.assertNotEqual(date_1, response.json['data']['date'])


def switch_to_tendering_by_auctionPeriod_startDate(self):
    self.set_status(
        'active.tendering', {
            'status': 'active.enquiries', "tenderPeriod": {}})
    self.app.authorization = ('Basic', ('chronograph', ''))
    response = self.app.patch_json(
        '/auctions/{}'.format(self.auction_id), {'data': {'id': self.auction_id}})
    self.assertEqual(response.status, '200 OK')
    self.assertNotEqual(response.json['data']["status"], "active.tendering")
    self.set_status(
        'active.tendering', {
            'status': self.initial_status, "enquiryPeriod": {}})
    response = self.app.patch_json(
        '/auctions/{}'.format(self.auction_id), {'data': {'id': self.auction_id}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']["status"], "active.tendering")


def switch_to_tendering_auctionPeriod(self):
    self.set_status(
        'active.tendering', {
            'status': 'active.enquiries', "tenderPeriod": {
                "startDate": None}})
    self.app.authorization = ('Basic', ('chronograph', ''))
    response = self.app.patch_json(
        '/auctions/{}'.format(self.auction_id), {'data': {'id': self.auction_id}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']["status"], "active.tendering")
    self.assertIn('auctionPeriod', response.json['data'])

# AuctionSwitchQualificationResourceTest


def switch_to_qualification(self):
    response = self.set_status(
        'active.auction', {
            'status': self.initial_status})
    self.app.authorization = ('Basic', ('chronograph', ''))
    response = self.app.patch_json(
        '/auctions/{}'.format(self.auction_id), {'data': {'id': self.auction_id}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "active.qualification")
    self.assertEqual(len(response.json['data']["awards"]), 1)
