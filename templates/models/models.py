from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Enum, ForeignKey, DECIMAL, DateTime
import enum
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Enum, ForeignKey, DECIMAL
from src.database.connection import Base
from sqlalchemy.orm import relationship


class ProductCategory(Base):
    __tablename__ = "product_categories"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    products = relationship("Product", backref="product_categories")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    stock = Column(Integer, nullable=False)
    minimumStock = Column(Integer, nullable=True)
    maximumStock = Column(Integer, nullable=True)
    reorderPoint = Column(Integer, nullable=True)
    category_id = Column(Integer, ForeignKey("product_categories.id"))
    provider = relationship(
        "Provider", secondary="provider_products", backref="products")
    movements = relationship("InventoryMovements", backref="products")
    orders = relationship("OrderItem", backref="products")


class ClientAddress(Base):
    __tablename__ = "client_address"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    address = Column(String(200), nullable=False)


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(50), nullable=False)
    address_id = relationship("ClientAddress", backref="clients")
    orders = relationship("Order", backref="clients")


class Provider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(50), nullable=False)
    address_id = relationship("ProviderAddress", backref="providers")


class ProviderAddress(Base):
    __tablename__ = "provider_address"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey("providers.id"))
    address = Column(String(200), nullable=False)


class ProviderProducts(Base):
    __tablename__ = "provider_products"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey("providers.id"))
    product_id = Column(Integer, ForeignKey("products.id"))


class Enum_Inventory(enum.Enum):
    ADD = "add"
    REMOVE = "remove"
    REORDER = "reorder"


class InventoryMovements(Base):
    __tablename__ = "inventory_movements"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    date = Column(TIMESTAMP)
    type = Column(Enum(Enum_Inventory))


class Enum_Status(enum.Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    CANCELED = "canceled"
    RETURNED = "returned"


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(TIMESTAMP)
    status = Column(Enum(Enum_Status))
    items = relationship("OrderItem", backref="orders")
    client_id = Column(Integer, ForeignKey("clients.id"))


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    total = Column(DECIMAL(10, 2), nullable=False)
