FROM python:latest@sha256:8488a4b1a393b0b2cb479a2da0a0d11cf816a77c0f9278205015148adadf9edf

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
