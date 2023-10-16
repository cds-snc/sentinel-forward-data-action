FROM python:latest@sha256:1615c71b5f3d48844b8d20cac4838f34267d96c3b061dcb6e4fda61a71599a9d

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
