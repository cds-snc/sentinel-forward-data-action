FROM python:latest@sha256:3a619e3c96fd4c5fc5e1998fd4dcb1f1403eb90c4c6409c70d7e80b9468df7df

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
