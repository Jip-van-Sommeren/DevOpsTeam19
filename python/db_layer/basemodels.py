from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

"""
CREATE TABLE item_stock (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (location_id) REFERENCES location(id)
);
"""


class ItemStock(Base):
    __tablename__ = "item_stock"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    quantity = Column(Integer, nullable=False)


"""
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    address TEXT NOT NULL,
    zip_code TEXT NOT NULL,
    city TEXT NOT NULL,
    street TEXT NOT NULL,
    state TEXT NOT NULL,
    number INTEGER NOT NULL,
    addition TEXT,
    type TEXT NOT NULL
);
"""


class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True)
    address = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    city = Column(String, nullable=False)
    street = Column(String, nullable=False)
    state = Column(String, nullable=False)
    number = Column(Integer, nullable=False)
    addition = Column(String)
    type = Column(String, nullable=False)


"""
# CREATE TABLE items (
#     id SERIAL PRIMARY KEY,
#     name VARCHAR(255) NOT NULL,
#     description TEXT NOT NULL,
#     price INTEGER NOT NULL DEFAULT 0
# );
"""


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    s3_key = Column(String)


"""
CREATE TABLE reservations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""


class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


"""
CREATE TABLE purchases (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    payment_token VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending'
    purchase_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""


class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    reservation_id = Column(Integer)
    payment_token = Column(String)
    status = Column(String, default="pending")
    purchase_date = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


"""
CREATE TABLE reserved_items (
    reservation_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (reservation_id, item_id),
    FOREIGN KEY (reservation_id) REFERENCES reservations(id)
);
"""


class ReservedItem(Base):
    __tablename__ = "reserved_items"
    reservation_id = Column(
        Integer, ForeignKey("reservations.id"), primary_key=True
    )
    item_id = Column(Integer, primary_key=True)
    quantity = Column(Integer, nullable=False)


"""
CREATE TABLE purchased_items (
    purchase_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (purchase_id, item_id),
    FOREIGN KEY (purchase_id) REFERENCES purchases(id)
);
"""


class PurchasedItem(Base):
    __tablename__ = "purchased_items"
    purchase_id = Column(Integer, ForeignKey("purchases.id"), primary_key=True)
    item_id = Column(Integer, primary_key=True)
    quantity = Column(Integer, nullable=False)
