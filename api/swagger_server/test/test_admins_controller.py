# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.item import Item  # noqa: E501
from swagger_server.models.reservation_update import ReservationUpdate  # noqa: E501
from swagger_server.models.warehouse import Warehouse  # noqa: E501
from swagger_server.test import BaseTestCase


class TestAdminsController(BaseTestCase):
    """AdminsController integration test stubs"""

    def test_create_item(self):
        """Test case for create_item

        Create new item
        """
        body = Item()
        response = self.client.open(
            '/items',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_create_warehouse(self):
        """Test case for create_warehouse

        Create new warehouse
        """
        body = Warehouse()
        response = self.client.open(
            '/location',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_item(self):
        """Test case for delete_item

        Delete item
        """
        response = self.client.open(
            '/items/{item_id}'.format(item_id='item_id_example'),
            method='DELETE')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_warehouse_info(self):
        """Test case for get_warehouse_info

        Get warehouse info
        """
        response = self.client.open(
            '/location',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_item(self):
        """Test case for update_item

        Update item
        """
        body = Item()
        response = self.client.open(
            '/items/{item_id}'.format(item_id='item_id_example'),
            method='PUT',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_reservation(self):
        """Test case for update_reservation

        Confirm or alter reservation (including changing to purchased)
        """
        body = ReservationUpdate()
        response = self.client.open(
            '/reservations/{reservation_id}'.format(reservation_id='reservation_id_example'),
            method='PUT',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
