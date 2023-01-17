FROM python:latest@sha256:5f004bbd8b9b6ae1478fee7d4dfbf38305af7188946aa79925667fa658458ba9

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
