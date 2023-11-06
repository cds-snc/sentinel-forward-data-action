FROM python:latest@sha256:7b8d65a924f596eb65306214f559253c468336bcae09fd575429774563460caf

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
