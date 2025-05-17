FROM python:latest@sha256:653b0cf8fc50366277a21657209ddd54edd125499d20f3520c6b277eb8c828d3

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
