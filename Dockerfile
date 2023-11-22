FROM python:latest@sha256:31ceea009f42df76371a8fb94fa191f988a25847a228dbeac35b6f8d2518a6ef

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
