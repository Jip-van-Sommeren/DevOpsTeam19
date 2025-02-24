# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.item import Item  # noqa: E501
from swagger_server.models.purchase_request import PurchaseRequest  # noqa: E501
from swagger_server.models.reservation_request import ReservationRequest  # noqa: E501
from swagger_server.test import BaseTestCase


class TestUsersController(BaseTestCase):
    """UsersController integration test stubs"""

    def test_get_item_stock_all_locations(self):
        """Test case for get_item_stock_all_locations

        Get stock of specific item for all locations
        """
        response = self.client.open(
            '/items/{item_id}'.format(item_id='item_id_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_item_stock_specific_location(self):
        """Test case for get_item_stock_specific_location

        Get stock of specific item for specific location
        """
        response = self.client.open(
            '/items/{item_id}/location/{location_id}'.format(item_id='item_id_example', location_id='location_id_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_items(self):
        """Test case for get_items

        Get list of all items
        """
        query_string = [('search_string', 'search_string_example'),
                        ('skip', 1),
                        ('limit', 50)]
        response = self.client.open(
            '/items',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_purchase_item(self):
        """Test case for purchase_item

        Purchase an item
        """
        body = PurchaseRequest()
        response = self.client.open(
            '/items/{item_id}/purchase'.format(item_id='item_id_example'),
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_reserve_item(self):
        """Test case for reserve_item

        Reserve item
        """
        body = ReservationRequest()
        response = self.client.open(
            '/items/{item_id}/reservations'.format(item_id='item_id_example'),
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_view_item_reservation(self):
        """Test case for view_item_reservation

        View reservation for an item
        """
        response = self.client.open(
            '/items/{item_id}/reservations'.format(item_id='item_id_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
