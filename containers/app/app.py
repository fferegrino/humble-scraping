import json
import os

import pandas as pd
import psycopg2
import streamlit as st
from anthropic import Anthropic
from sentence_transformers import SentenceTransformer

st.set_page_config(page_title="Humble Bundle Search", page_icon="🛒", layout="wide")

DISTANCE_THRESHOLD = 3

client = Anthropic()

with open("intent-prompt.txt") as f:
    PROMPT = f.read()

model = SentenceTransformer(os.environ["MODEL_PATH"])


def get_vector(text: str):
    vector = model.encode(text).tolist()
    return f"[{','.join(map(str, vector))}]"


db_settings = {
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "root"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "humble_data"),
}


def get_conn():
    return psycopg2.connect(**db_settings)


def bundle_query_builder(fields: list, intent: dict):
    query_embedding = get_vector(intent["query"])
    conditions.append(f"description_embedding <-> '{query_embedding}' < {DISTANCE_THRESHOLD}")

    if intent["ebook"]:
        conditions.append("media_type = 'ebook'")
    elif intent["game"]:
        conditions.append("media_type = 'game'")
    elif intent["software"]:
        conditions.append("media_type = 'software'")

    if intent["current"]:
        conditions.append("now() < end_date")

    sep = "\n\t"
    conditions_str = (sep + "AND ").join(conditions)
    query = f"""
SELECT {("," + sep).join(fields)}
FROM bundle
WHERE {conditions_str}
ORDER BY
    description_embedding <-> '{query_embedding}'
LIMIT 10
""".strip()

    return query


def get_intent(query: str):
    message = client.messages.create(
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": PROMPT.replace("{{USER_QUERY}}", query),
            }
        ],
        model="claude-3-5-sonnet-latest",
    )
    return json.loads(message.content[0].text)


st.title("Humble Bundle Search")

query = st.text_input("Enter your query")

if query:
    intent = get_intent(query)

    if intent["intent"] == "bundle":
        conditions = []
        fields = [
            "machine_name",
            "author",
            "human_name",
            "description",
            "start_date",
            "end_date",
            "media_type",
            "url",
        ]

        query = bundle_query_builder(fields, intent)

        with get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                dicts = [dict(zip(fields, result)) for result in results]

        with st.expander("Debug info"):
            left, right = st.columns(2)
            with left:
                st.code(query)
            with right:
                st.json(intent)

        for result in dicts:
            st.subheader(result["human_name"])
            st.markdown(f"**{result['author']}**")
            st.html(result["description"])
            st.link_button("View bundle", url="https://www.humblebundle.com" + result["url"])

    elif intent["intent"] == "charity":
        st.error("Charity-specific queries are not supported yet")

    elif intent["intent"] == "item":
        st.error("Item-specific queries are not supported yet")
