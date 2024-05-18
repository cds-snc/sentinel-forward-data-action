FROM python:latest@sha256:3966b81808d864099f802080d897cef36c01550472ab3955fdd716d1c665acd6

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
