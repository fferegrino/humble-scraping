import json
from collections import defaultdict, namedtuple
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from magiccionary import keep_keys

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

Entry = namedtuple("Entry", ["query_time", "kind", "url", "content"])

query_time = datetime.now()
query_time_str = query_time.isoformat()

keep_keys_list = [
    "machine_name",
    "author",
    # "at_time|datetime",
    [
        "basic_data",
        [
            "eula",
            "human_name",
            "detailed_marketing_blurb",
            "short_marketing_blurb",
            "media_type",
            "description",
            "legal_disclaimer",
            "required_account_links",
            "end_time|datetime",
        ],
    ],
    [
        "tier_item_data",
        "*",
        [
            "human_name" "machine_name",
            "youtube_link",
            "callout",
            "publishers",
            "side_box_art_text",
            "third_party_subscribe_text",
            "msrp_price",
            "min_price|money",
            "subtitle_html",
            "description_text",
            "user_ratings",
            "developers",
            "item_content_type",
        ],
    ],
    [
        "charity_data",
        "charity_items",
        "*",
        [
            "machine_name",
            "youtube_link",
            "item_content_type",
            "subtitle_html",
            "description_text",
            "human_name",
            "developers",
            "publishers",
            "user_ratings",
        ],
    ],
]


def load_js_data(page, script_id, extract_key=None):
    script_id = script_id.lstrip("/")
    page = requests.get(f"https://www.humblebundle.com/{page}")
    soup = BeautifulSoup(page.content, "html.parser")
    data = json.loads(soup.find("script", {"id": script_id}).text)
    if extract_key:
        data = data[extract_key]
    return data


all_bundles_data = load_js_data("bundles", "landingPage-json-data", "data")


kept = keep_keys(
    all_bundles_data,
    [
        [
            "*",
            "mosaic",
            "[]",
            "products",
            "[]",
            [
                "machine_name",
                "tile_short_name",
                "short_marketing_blurb",
                "marketing_blurb",
                "detailed_marketing_blurb",
                "author",
                "start_date|datetime",
                "end_date|datetime",
                "type",
                "product_url",
            ],
        ],
    ],
)


perserved_all_bundles_data = {}
for k in kept.keys():
    perserved_all_bundles_data[k] = kept[k]["mosaic"][0]["products"]


product_data_list = []
for kind in perserved_all_bundles_data.keys():
    for product in perserved_all_bundles_data[kind]:
        product["start_date|datetime"] = datetime.strptime(product["start_date|datetime"][:19], "%Y-%m-%dT%H:%M:%S")
        product["end_date|datetime"] = datetime.strptime(product["end_date|datetime"][:19], "%Y-%m-%dT%H:%M:%S")
        product_data = load_js_data(product["product_url"], "webpack-bundle-page-data", "bundleData")
        product_data = keep_keys(product_data, keep_keys_list)
        try:
            product_data["basic_data"]["end_time|datetime"] = datetime.strptime(
                product_data["basic_data"]["end_time|datetime"][:19], "%Y-%m-%dT%H:%M:%S"
            )
        except:
            print("No end date found")
            pass
        product_data["from_bundle"] = product
        product_data_list.append(product_data)


class DateTimeCodec(json.JSONEncoder):
    def __init__(self, datetime_fields=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datetime_fields = set(datetime_fields or [])

    def default(self, obj):
        return obj.isoformat() if isinstance(obj, datetime) else super().default(obj)

    def decode(self, obj):
        return {
            k: datetime.fromisoformat(v) if k in self.datetime_fields and isinstance(v, str) else v
            for k, v in obj.items()
        }


def bucket_products_monthly(products):
    monthly_buckets = defaultdict(list)
    sorted_products = sorted(products, key=lambda x: x["from_bundle"]["start_date|datetime"], reverse=True)

    for article in sorted_products:
        article_date = article["from_bundle"]["start_date|datetime"].date()
        start_of_month = datetime(article_date.year, article_date.month, 1)
        monthly_buckets[start_of_month].append(article)

    sorted_monthly_buckets = dict(sorted(monthly_buckets.items(), reverse=True))

    return sorted_monthly_buckets


from magiccionary.magic import nested_update

exec_time = datetime.now()
datetime_fields = ["start_date|datetime", "end_date|datetime", "end_time|datetime", "updated_at|datetime"]


def write_monthly_data(date, updated_records):

    target_file = data_dir / f'bundles-{date.strftime("%Y-%m")}.jsonl'
    current_records = {}
    updated_at = {}
    first_seen_at = {}

    if target_file.exists():
        with open(target_file) as f:
            for line in f:
                record = json.loads(line, object_hook=DateTimeCodec(datetime_fields).decode)
                updated_at[record["machine_name"]] = record.pop("updated_at|datetime")
                first_seen_at[record["machine_name"]] = record.pop("first_seen_at|datetime")
                current_records[record["machine_name"]] = record

    for record in updated_records:
        if record["machine_name"] in current_records:
            if current_records[record["machine_name"]] != record:
                current_records[record["machine_name"]] = nested_update(current_records[record["machine_name"]], record)
                updated_at[record["machine_name"]] = exec_time
        else:
            current_records[record["machine_name"]] = record
            updated_at[record["machine_name"]] = exec_time
            first_seen_at[record["machine_name"]] = exec_time

    sorted_records = sorted(
        current_records.values(),
        key=lambda x: (x["from_bundle"]["start_date|datetime"], x["machine_name"]),
        reverse=True,
    )
    with open(target_file, "w") as f:
        for record in sorted_records:
            record["updated_at|datetime"] = updated_at[record["machine_name"]]
            record["first_seen_at|datetime"] = first_seen_at[record["machine_name"]]
            f.write(json.dumps(record, cls=DateTimeCodec, datetime_fields=datetime_fields) + "\n")


buckets = bucket_products_monthly(product_data_list)
for date, records in buckets.items():
    write_monthly_data(date, records)
