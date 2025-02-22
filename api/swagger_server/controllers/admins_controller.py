import connexion
import six

from swagger_server.models.item import Item  # noqa: E501
from swagger_server.models.location import Location  # noqa: E501
from swagger_server import util


def add_item(body=None):  # noqa: E501
    """adds an inventory item

    Adds an item to the system # noqa: E501

    :param body: InventoryItem to add
    :type body: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        body = Item.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def add_location(body=None):  # noqa: E501
    """add a location

     # noqa: E501

    :param body: 
    :type body: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        body = Location.from_dict(connexion.request.get_json())  # noqa: E501
        print(body)
    return 'do some magic!'


def delete_item_by_id(id):  # noqa: E501
    """delete an item

     # noqa: E501

    :param id: 
    :type id: str

    :rtype: None
    """
    return 'do some magic!'


def get_location():  # noqa: E501
    """searches locations

    By passing in the appropriate options, you can search for locations in the system  # noqa: E501


    :rtype: None
    """
    return 'do some magic!'


def update_item_by_id(id):  # noqa: E501
    """update an item

     # noqa: E501

    :param id: 
    :type id: str

    :rtype: None
    """
    return 'do some magic!'
