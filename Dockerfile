FROM python:latest@sha256:b7a504dd0affeb20cf1ba1d3219f854c889c7ad557a2a5a4c4aba19cadd075f1

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
