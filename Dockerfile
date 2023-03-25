FROM python:latest@sha256:5329e75033c4446dc92d702cf8ebbeb63e549d9b83076a776f6753e10817fc3c

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
