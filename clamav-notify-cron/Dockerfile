FROM python:3-alpine

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY main.py ./

RUN addgroup -g 1000 -S app && adduser -u 1000 -S app -G app

USER 1000

ENTRYPOINT ["./main.py"]
