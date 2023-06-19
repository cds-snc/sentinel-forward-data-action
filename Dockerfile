FROM python:latest@sha256:2dd2f9000021839e8fba0debd8a2308c7e26f95fdfbc0c728eeb0b5b9a8c6a39

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
