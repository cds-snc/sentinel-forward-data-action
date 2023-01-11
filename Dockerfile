FROM python:latest

WORKDIR /src

ENV PYTHONPATH /src

COPY src/requirements.txt . 

RUN pip install -r requirements.txt

COPY . /src 

CMD ["python", "/src/action.py"]
