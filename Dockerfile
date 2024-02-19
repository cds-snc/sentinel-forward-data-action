FROM python:latest@sha256:e83d1f4d0c735c7a54fc9dae3cca8c58473e3b3de08fcb7ba3d342ee75cfc09d

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
