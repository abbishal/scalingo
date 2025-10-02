FROM python:3.8.2

RUN apt-get update && apt-get install --yes python3-pip
WORKDIR /usr/src/app

COPY ./ /usr/src/app/
RUN pip install requests
CMD python app.py
