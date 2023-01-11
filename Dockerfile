FROM python:latest

RUN pwd && ls

ADD src .

COPY . .

RUN pwd && ls

RUN pip install -r requirements.txt

RUN pwd && ls

CMD ["python", "src/action.py"]
