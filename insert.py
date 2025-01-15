from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pathlib import Path
import json
from models import Charity, BundleItem, Bundle

DATABASE_URL = "sqlite:///db2.db"

engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)
session = Session()

data = Path("data")

all_entities = []

bundles = []
for bundle_file in data.glob("bundles-*.jsonl"):
    with open(bundle_file) as f:
        for line in f:
            bundles.append(json.loads(line))

for bundle in bundles:

    existing_bundle = session.query(Bundle).filter_by(
        machine_name=bundle['machine_name']
    ).first()

    if existing_bundle:
        print("Skipping existing bundle", bundle['machine_name'])
        continue

    charities = []
    existing_charities = set()

    for machine_name, charity in bundle['charity_data']['charity_items'].items():
        existing_charity = session.query(Charity).filter_by(
            machine_name=machine_name
        ).first()

        if not existing_charity:
            existing_charity = Charity(
                machine_name=machine_name,
                human_name=charity['human_name'],
                description=charity['description_text']
            )

        existing_charities.add(machine_name)
        charities.append(existing_charity)
        session.add(existing_charity)

    items = []
    for machine_name, item in bundle['tier_item_data'].items():
        if machine_name in existing_charities:
            continue
        
        existing_item = session.query(BundleItem).filter_by(
            machine_name=machine_name
        ).first()

        if not existing_item:
            existing_item = BundleItem(
                machine_name=machine_name,
                human_name=item['human_name'],
                description=item['description_text']
            )

        items.append(existing_item)
        session.add(existing_item)

    bb = Bundle(
            machine_name=bundle['machine_name'],
            human_name=bundle['basic_data']['human_name'],
            detailed_marketing_blurb=bundle['basic_data']['detailed_marketing_blurb'],
            short_marketing_blurb=bundle['basic_data']['short_marketing_blurb'],
            media_type=bundle['basic_data']['media_type'],
            author=bundle['author'],
            name=bundle['from_bundle']['tile_short_name'],
            start_date=datetime.fromisoformat(
                bundle['from_bundle']['start_date|datetime']
            ),
            end_date=datetime.fromisoformat(
                bundle['from_bundle']['end_date|datetime']
            ),
            url=bundle['from_bundle']['product_url'],
            bundle_items=items,
            charities=charities
        )
    session.add(bb)
    session.commit()
session.close()
