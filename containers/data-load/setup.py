import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import psycopg2
from sentence_transformers import SentenceTransformer

from shared import Bundle, Charity, Item

db_settings = {
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "database": os.getenv("POSTGRES_DB"),
}
model = SentenceTransformer(os.environ["MODEL_PATH"])

vector_cache = {}

# Load cache from file
if Path("/vector_cache/cache.json").exists():
    with open("/vector_cache/cache.json", "r") as f:
        vector_cache = json.load(f)


def get_vector(key: str, text: str):
    if key in vector_cache:
        return np.array(vector_cache[key]).tolist()
    vector = model.encode(text)
    vector_cache[key] = vector.tolist()
    return vector.tolist()


conn = psycopg2.connect(**db_settings)

with conn.cursor() as cursor:
    print("Creating extension")
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.commit()


with conn.cursor() as cursor:
    print("Creating bundle table")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bundle (
            machine_name VARCHAR(255) PRIMARY KEY,
            author VARCHAR(255),
            human_name VARCHAR(255),
            description TEXT,
            detailed_marketing_blurb TEXT,
            short_marketing_blurb TEXT,
            media_type VARCHAR(255),
            name VARCHAR(255),
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            url VARCHAR(255),
            description_embedding vector(768)
        )
        """
    )
    print("Creating item table")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS item (
            machine_name VARCHAR(255) PRIMARY KEY,
            human_name VARCHAR(255),
            description TEXT,
            description_embedding vector(768)
        )
        """
    )

    print("Creating charity table")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS charity (
            machine_name VARCHAR(255) PRIMARY KEY,
            human_name VARCHAR(255),
            description TEXT,
            description_embedding vector(768)
        )
        """
    )

    print("Creating item-bundle relationship table")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bundle_item (
            bundle_id VARCHAR(255),
            item_id VARCHAR(255),
            PRIMARY KEY (bundle_id, item_id)
        )
        """
    )

    print("Creating charity-bundle relationship table")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS charity_bundle (
            charity_id VARCHAR(255),
            bundle_id VARCHAR(255),
            PRIMARY KEY (charity_id, bundle_id)
        )
        """
    )
    conn.commit()


data_dir = Path("data")

for file in data_dir.glob("bundles-*.jsonl"):
    with open(file, "r") as f:
        for line in f:
            bundle = json.loads(line)

            existing_charities = set()
            charities_in_bundle = []

            for machine_name, charity in bundle["charity_data"]["charity_items"].items():
                with conn.cursor() as cursor:
                    existing_charity = cursor.execute("SELECT * FROM charity WHERE machine_name = %s", (machine_name,))
                if cursor.rowcount == 0:
                    print(f"Charity {machine_name} not found, creating")
                    existing_charity = Charity(
                        machine_name=machine_name,
                        human_name=charity["human_name"],
                        description=charity["description_text"],
                        description_embedding=get_vector(machine_name, charity["description_text"]),
                    )
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO charity (machine_name, human_name, description, description_embedding) VALUES (%s, %s, %s, %s)",
                            (
                                existing_charity.machine_name,
                                existing_charity.human_name,
                                existing_charity.description,
                                existing_charity.description_embedding,
                            ),
                        )
                        conn.commit()
                charities_in_bundle.append(machine_name)

            items_in_bundle = []

            with conn.cursor() as cursor:
                for machine_name, item in bundle["tier_item_data"].items():
                    existing_item = cursor.execute("SELECT * FROM item WHERE machine_name = %s", (machine_name,))
                    if cursor.rowcount == 0:
                        existing_item = Item(
                            machine_name=machine_name,
                            human_name=item["human_name"],
                            description=item["description_text"],
                            description_embedding=get_vector(machine_name, item["description_text"]),
                        )
                        cursor.execute(
                            "INSERT INTO item (machine_name, human_name, description, description_embedding) VALUES (%s, %s, %s, %s)",
                            (
                                existing_item.machine_name,
                                existing_item.human_name,
                                existing_item.description,
                                existing_item.description_embedding,
                            ),
                        )
                        conn.commit()
                    items_in_bundle.append(machine_name)

            bundle_obj = Bundle(
                machine_name=bundle["machine_name"],
                human_name=bundle["basic_data"]["human_name"],
                description=bundle["basic_data"]["description"],
                detailed_marketing_blurb=bundle["basic_data"]["detailed_marketing_blurb"],
                short_marketing_blurb=bundle["basic_data"]["short_marketing_blurb"],
                media_type=bundle["basic_data"]["media_type"],
                author=bundle["author"],
                name=bundle["from_bundle"]["tile_short_name"],
                start_date=datetime.fromisoformat(bundle["from_bundle"]["start_date|datetime"]),
                end_date=datetime.fromisoformat(bundle["from_bundle"]["end_date|datetime"]),
                url=bundle["from_bundle"]["product_url"],
                description_embedding=get_vector(bundle["machine_name"], bundle["basic_data"]["description"]),
            )

            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM bundle WHERE machine_name = %s", (bundle_obj.machine_name,))
                if cursor.rowcount == 0:
                    cursor.execute(
                        "INSERT INTO bundle (machine_name, author, human_name, description, detailed_marketing_blurb, short_marketing_blurb, media_type, name, start_date, end_date, url, description_embedding) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (
                            bundle_obj.machine_name,
                            bundle_obj.author,
                            bundle_obj.human_name,
                            bundle_obj.description,
                            bundle_obj.detailed_marketing_blurb,
                            bundle_obj.short_marketing_blurb,
                            bundle_obj.media_type,
                            bundle_obj.name,
                            bundle_obj.start_date,
                            bundle_obj.end_date,
                            bundle_obj.url,
                            bundle_obj.description_embedding,
                        ),
                    )
                conn.commit()

            for charity in charities_in_bundle:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM charity_bundle WHERE charity_id = %s AND bundle_id = %s",
                        (charity, bundle_obj.machine_name),
                    )
                    if cursor.rowcount == 0:
                        cursor.execute(
                            "INSERT INTO charity_bundle (charity_id, bundle_id) VALUES (%s, %s)",
                            (charity, bundle_obj.machine_name),
                        )
                        conn.commit()

            for item in items_in_bundle:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM bundle_item WHERE bundle_id = %s AND item_id = %s",
                        (bundle_obj.machine_name, item),
                    )
                    if cursor.rowcount == 0:
                        cursor.execute(
                            "INSERT INTO bundle_item (bundle_id, item_id) VALUES (%s, %s)",
                            (bundle_obj.machine_name, item),
                        )
                        conn.commit()
# Save cache to file
with open("/vector_cache/vector_cache.json", "w") as f:
    json.dump(vector_cache, f)
