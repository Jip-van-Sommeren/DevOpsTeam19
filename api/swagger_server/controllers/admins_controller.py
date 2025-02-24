import connexion
import six

from swagger_server.models.item import Item  # noqa: E501
from swagger_server.models.reservation_update import ReservationUpdate  # noqa: E501
from swagger_server.models.warehouse import Warehouse  # noqa: E501
from swagger_server import util


def create_item(body):  # noqa: E501
    """Create new item

     # noqa: E501

    :param body: Item to add
    :type body: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        body = Item.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def create_warehouse(body):  # noqa: E501
    """Create new warehouse

     # noqa: E501

    :param body: Warehouse to add
    :type body: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        body = Warehouse.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def delete_item(item_id):  # noqa: E501
    """Delete item

     # noqa: E501

    :param item_id: 
    :type item_id: str

    :rtype: None
    """
    return 'do some magic!'


def get_warehouse_info():  # noqa: E501
    """Get warehouse info

     # noqa: E501


    :rtype: None
    """
    return 'do some magic!'


def update_item(body, item_id):  # noqa: E501
    """Update item

     # noqa: E501

    :param body: Item update payload
    :type body: dict | bytes
    :param item_id: 
    :type item_id: str

    :rtype: None
    """
    if connexion.request.is_json:
        body = Item.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_reservation(body, reservation_id):  # noqa: E501
    """Confirm or alter reservation (including changing to purchased)

     # noqa: E501

    :param body: Reservation update details
    :type body: dict | bytes
    :param reservation_id: 
    :type reservation_id: str

    :rtype: None
    """
    if connexion.request.is_json:
        body = ReservationUpdate.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
