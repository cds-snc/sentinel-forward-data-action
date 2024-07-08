FROM python:latest@sha256:d12b529fba98bcc93e2e2e837c0a60efaa6328775965a43c1b8161cfbd8f10f3

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
