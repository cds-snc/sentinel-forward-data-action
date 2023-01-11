FROM python:latest

RUN pwd && ls

WORKDIR /src

ENV PYTHONPATH /src

RUN pwd && ls

COPY src/requirements.txt . 

RUN pip install -r requirements.txt

COPY . /src 

RUN pwd && ls

CMD ["python", "/src/action.py"]
