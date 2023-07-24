FROM python:latest@sha256:d73088ce13d5a1eec1dd05b47736041ae6921d08d2f240035d99642db98bc8d4

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
