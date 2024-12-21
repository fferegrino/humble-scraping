from dataclasses import dataclass
from datetime import datetime
from typing import Any

VECTOR_DIMENSION = 768


@dataclass
class Bundle:
    machine_name: str
    author: str
    human_name: str
    description: str
    detailed_marketing_blurb: str
    short_marketing_blurb: str
    media_type: str
    name: str
    start_date: datetime
    end_date: datetime
    url: str
    description_embedding: Any = None


@dataclass
class Item:
    machine_name: str
    human_name: str
    description: str
    description_embedding: Any = None


@dataclass
class Charity:
    machine_name: str
    human_name: str
    description: str
    description_embedding: Any = None
