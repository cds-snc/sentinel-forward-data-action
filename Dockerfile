FROM python:latest@sha256:7adb2f6d6b0fdaf2d3029c42b5a40833589f969c18728f5b5b126a61394848b6

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
