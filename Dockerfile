FROM python:latest@sha256:85b3d192dddbc96588b719e86991e472b390805a754681a38132de1977d8e429

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
