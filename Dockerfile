FROM python:latest@sha256:fe68f3194a1a6df058901085495abca83d8841415101366c3a4c66f06f39760a

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
