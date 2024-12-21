import os

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
model.save(os.environ["MODEL_PATH"])
