FROM python:latest@sha256:f7382f4f9dbc51183c72d621b9c196c1565f713a1fe40c119d215c961fa22815

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
