FROM python:latest@sha256:f78ea8a345769eb3aa1c86cf147dfd68f1a4508ed56f9d7574e4687b02f44dd1

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
