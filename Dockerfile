FROM python:3.6

RUN mkdir -p /src
WORKDIR /src

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

CMD bash
