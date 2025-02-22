import connexion
import six

from swagger_server.models.item import Item  # noqa: E501
from swagger_server import util


def buy_item(id):  # noqa: E501
    """buy an inventory item

    Buy an item # noqa: E501

    :param id: 
    :type id: str

    :rtype: None
    """
    return 'do some magic!'


def get_item_by_id(id):  # noqa: E501
    """get item by id

     # noqa: E501

    :param id: 
    :type id: str

    :rtype: None
    """
    return 'do some magic!'


def get_items(search_string=None, skip=None, limit=None):  # noqa: E501
    """searches items

    By passing in the appropriate options, you can search for available inventory in the system  # noqa: E501

    :param search_string: pass an optional search string for looking up inventory
    :type search_string: str
    :param skip: number of records to skip for pagination
    :type skip: int
    :param limit: maximum number of records to return
    :type limit: int

    :rtype: List[Item]
    """
    return 'do some magic!'
