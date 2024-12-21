FROM python:3.11-slim

WORKDIR /app

COPY ./containers/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV MODEL_PATH=/app/model.bin

COPY ./containers/api/model_setup.py model_setup.py

RUN python model_setup.py

COPY ./containers/api/app.py ./containers/api/intent-prompt.txt ./

CMD ["streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "0.0.0.0"]
