FROM python:latest@sha256:c7862834f921957523cc4dab6d7795a7a0d19f1cd156c1ecd3a3a08c1108c9a4

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
