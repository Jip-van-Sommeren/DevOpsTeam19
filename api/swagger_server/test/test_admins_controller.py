# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.item import Item  # noqa: E501
from swagger_server.models.location import Location  # noqa: E501
from swagger_server.test import BaseTestCase


class TestAdminsController(BaseTestCase):
    """AdminsController integration test stubs"""

    def test_add_item(self):
        """Test case for add_item

        adds an inventory item
        """
        body = Item()
        response = self.client.open(
            '/items',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_add_location(self):
        """Test case for add_location

        add a location
        """
        body = Location()
        response = self.client.open(
            '/location',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_item_by_id(self):
        """Test case for delete_item_by_id

        delete an item
        """
        response = self.client.open(
            '/items/{id}'.format(id='id_example'),
            method='DELETE')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_location(self):
        """Test case for get_location

        searches locations
        """
        response = self.client.open(
            '/location',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_item_by_id(self):
        """Test case for update_item_by_id

        update an item
        """
        response = self.client.open(
            '/items/{id}'.format(id='id_example'),
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
