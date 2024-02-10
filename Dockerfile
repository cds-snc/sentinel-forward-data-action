FROM python:latest@sha256:5eda1a3e78a90e7542c221cf525233f4b958a5778e61bcc350cc1e0d2bcf7ecf

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
