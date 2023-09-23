FROM python:latest@sha256:2e376990a11f1c1e03796d08db0e99c36eadb4bb6491372b227f1e53c3482914

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
