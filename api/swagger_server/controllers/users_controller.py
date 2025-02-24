import connexion
import six

from swagger_server.models.item import Item  # noqa: E501
from swagger_server.models.purchase_request import PurchaseRequest  # noqa: E501
from swagger_server.models.reservation_request import ReservationRequest  # noqa: E501
from swagger_server import util


def get_item_stock_all_locations(item_id):  # noqa: E501
    """Get stock of specific item for all locations

     # noqa: E501

    :param item_id: 
    :type item_id: str

    :rtype: None
    """
    return 'do some magic!'


def get_item_stock_specific_location(item_id, location_id):  # noqa: E501
    """Get stock of specific item for specific location

     # noqa: E501

    :param item_id: 
    :type item_id: str
    :param location_id: 
    :type location_id: str

    :rtype: None
    """
    return 'do some magic!'


def get_items(search_string=None, skip=None, limit=None):  # noqa: E501
    """Get list of all items

     # noqa: E501

    :param search_string: Optional search string for filtering inventory
    :type search_string: str
    :param skip: Number of records to skip for pagination
    :type skip: int
    :param limit: Maximum number of records to return
    :type limit: int

    :rtype: List[Item]
    """
    return 'do some magic!'


def purchase_item(body, item_id):  # noqa: E501
    """Purchase an item

     # noqa: E501

    :param body: Purchase request with header-tied details
    :type body: dict | bytes
    :param item_id: 
    :type item_id: str

    :rtype: None
    """
    if connexion.request.is_json:
        body = PurchaseRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def reserve_item(body, item_id):  # noqa: E501
    """Reserve item

     # noqa: E501

    :param body: Reservation details for the item
    :type body: dict | bytes
    :param item_id: 
    :type item_id: str

    :rtype: None
    """
    if connexion.request.is_json:
        body = ReservationRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def view_item_reservation(item_id):  # noqa: E501
    """View reservation for an item

     # noqa: E501

    :param item_id: 
    :type item_id: str

    :rtype: None
    """
    return 'do some magic!'
