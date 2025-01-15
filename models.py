from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table
from datetime import datetime

# Define the database connection string
DATABASE_URL = "sqlite:///db2.db"

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a base class for declarative models
Base = declarative_base()

# Define the Charity model
class Charity(Base):
    __tablename__ = "charities"

    machine_name = Column(String, primary_key=True, index=True)
    human_name = Column(String)
    description = Column(String)

# Define the BundleItem model
class BundleItem(Base):
    __tablename__ = "bundle_items"

    machine_name = Column(String, primary_key=True, index=True)
    human_name = Column(String)
    description = Column(String)

# Define the Bundle model
class Bundle(Base):
    __tablename__ = "bundles"

    machine_name = Column(String, primary_key=True, index=True)
    author = Column(String)
    human_name = Column(String)
    detailed_marketing_blurb = Column(String)
    short_marketing_blurb = Column(String)
    media_type = Column(String)
    name = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    url = Column(String)

# Define the association tables for many-to-many relationships
bundle_charity_association = Table(
    "bundle_charity_association",
    Base.metadata,
    Column("bundle_machine_name", String, ForeignKey("bundles.machine_name")),
    Column("charity_machine_name", String, ForeignKey("charities.machine_name")),
)

bundle_bundle_item_association = Table(
    "bundle_bundle_item_association",
    Base.metadata,
    Column("bundle_machine_name", String, ForeignKey("bundles.machine_name")),
    Column("bundle_item_machine_name", String, ForeignKey("bundle_items.machine_name")),
)

# Add relationships to the models
Charity.bundles = relationship(
    "Bundle", secondary=bundle_charity_association, back_populates="charities"
)
Bundle.charities = relationship(
    "Charity", secondary=bundle_charity_association, back_populates="bundles"
)

Bundle.bundle_items = relationship(
    "BundleItem", secondary=bundle_bundle_item_association, back_populates="bundles"
)
BundleItem.bundles = relationship(
    "Bundle", secondary=bundle_bundle_item_association, back_populates="bundle_items"
)

# Create the database tables
Base.metadata.create_all(engine)
