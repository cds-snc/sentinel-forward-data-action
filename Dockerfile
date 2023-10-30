FROM python:latest@sha256:2586dd7abe015eeb6673bc66d18f0a628a997c293b41268bc981e826bc0b5a92

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
