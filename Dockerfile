FROM python:latest@sha256:99861e7d72be0890bb5912d4ff280bf9060eccb422abf3cf600162552d8c2cdc

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
