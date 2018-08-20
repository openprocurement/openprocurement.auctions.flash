from openprocurement.auctions.core.utils import get_now
from datetime import timedelta
from openprocurement.auctions.core.plugins.contracting.v3.models import (
    Prolongation,
)

PARTIAL_MOCK_CONFIG = {
    "auctions.flash": {
        "use_default": True,
        "plugins": {
            "flash.migration": None
        },
        "migration": False,
        "aliases": []
    }
}

PROLONGATION = {
    'decisionID': 'very_importante_documente',
    'description': 'Prolongate your contract for free!',
    'reason': 'other',
    'documents': [],
    'datePublished': get_now().isoformat(),
}


def create_award(test_case):
    # Create award
    authorization = test_case.app.authorization
    test_case.app.authorization = ('Basic', ('auction', ''))
    now = get_now()
    if test_case.initial_lots:
        auction_result = {
            'bids': [
                {
                    "id": b['id'],
                    "date": (now - timedelta(seconds=i)).isoformat(),
                    "lotValues": [{'value': item['value']} for item in b['lotValues']]
                }
                for i, b in enumerate(test_case.initial_bids)
            ]
        }
        auction = test_case.db.get(test_case.auction_id)
        for lot in auction['lots']:
            lot.update({
                "auctionPeriod": {
                    "startDate": (now - timedelta(days=1)).isoformat(),
                    "endDate": now.isoformat()
                }
            })
        test_case.db.save(auction)
    else:
        auction_result = {
            'bids': [
                {
                    "id": b['id'],
                    "date": (now - timedelta(seconds=i)).isoformat(),
                    "value": b['value']
                }
                for i, b in enumerate(test_case.initial_bids)
            ]
        }

    response = test_case.app.post_json(
        '/auctions/{}/auction'.format(test_case.auction_id),
        {'data': auction_result}
    )
    auction = response.json['data']
    test_case.assertEqual(response.status, '200 OK')
    test_case.assertEqual('active.qualification', auction["status"])
    test_case.first_award = auction['awards'][0]
    test_case.award = auction['awards'][0]
    # test_case.second_award = auction['awards'][1]
    test_case.first_award_id = test_case.first_award['id']
    test_case.award_id = test_case.first_award_id
    # test_case.second_award_id = test_case.second_award['id']
    test_case.first_bid_token = test_case.initial_bids_tokens.items()[0][1]
    test_case.second_bid_token = test_case.initial_bids_tokens.items()[1][1]
    test_case.app.authorization = authorization

    # response = test_case.app.post(
    #     '/auctions/{}/awards/{}/documents?acc_token={}'.format(
    #         test_case.auction_id,
    #         test_case.award_id,
    #         test_case.auction_token
    #     ),
    #     upload_files=[('file', 'auction_protocol.pdf', 'content')]
    # )
    # test_case.assertEqual(response.status, '201 Created')
    # test_case.assertEqual(response.content_type, 'application/json')
    # doc_id = response.json["data"]['id']
    #
    # response = test_case.app.patch_json(
    #     '/auctions/{}/awards/{}/documents/{}?acc_token={}'.format(
    #         test_case.auction_id,
    #         test_case.award_id,
    #         doc_id,
    #         test_case.auction_token
    #     ),
    #     {"data": {
    #         "description": "auction protocol",
    #         "documentType": 'auctionProtocol'
    #     }}
    # )
    # test_case.assertEqual(response.status, '200 OK')
    # test_case.assertEqual(response.content_type, 'application/json')
    # test_case.assertEqual(
    #     response.json["data"]["documentType"],
    #     'auctionProtocol'
    # )
    # test_case.assertEqual(response.json["data"]["author"], 'auction_owner')
    #
    # test_case.app.patch_json(
    #     '/auctions/{}/awards/{}'.format(
    #         test_case.auction_id,
    #         test_case.award_id
    #     ),
    #     {"data": {"status": "pending"}}
    # )
    # test_case.app.patch_json(
    #     '/auctions/{}/awards/{}'.format(
    #         test_case.auction_id,
    #         test_case.award_id
    #     ),
    #     {"data": {"status": "active"}}
    # )
    # get_auction_response = test_case.app.get(
    #     '/auctions/{}'c.format(
    #         test_case.auction_id,
    #     )
    # )
    # test_case.award_contract_id = get_auction_response.\
    #     json['data']['contracts'][0]['id']


def create_prolongation(test_case, test_case_attr):
    """Create prolongation and place it's id into test_case arrtibute
    """
    prolongation_post_response = test_case.app.post_json(
        '/auctions/{0}/contracts/{1}/prolongations'.format(
            test_case.auction_id,
            test_case.contract_id
        ),
        {'data': PROLONGATION}
    )
    test_case.assertEqual(prolongation_post_response.status, '201 Created')

    prolongation_data = prolongation_post_response.json.get('data', {})
    created_prolongation = Prolongation(prolongation_data)
    created_prolongation.validate()  # check returned data
    test_case.assertEqual(
        created_prolongation.decisionID,
        PROLONGATION['decisionID'],
        'Prolongation creation is wrong.'
    )
    setattr(test_case, test_case_attr, created_prolongation.id)
