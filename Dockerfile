FROM python:latest@sha256:785fef11f44b7393c03d77032fd72e56af8b05442b051a151229145e5fbbcb29

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
