FROM python:latest@sha256:db831623299f8eaef6c8bcb8f0f356fd8384bd0db13c28ff671c3cf562a58db7

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
