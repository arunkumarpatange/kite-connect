FROM ubuntu:14.04

RUN apt-get update && apt-get install -y build-essential \
    software-properties-common \
    python-software-properties \
    python-dev \
    python-pip \
    wget libfreetype6 libfreetype6-dev libfontconfig1 libfontconfig1-dev

ADD . /app
WORKDIR /app

RUN cd /usr/local/share && \
    tar xjf /app/phantomjs-2.1.1-linux-x86_64.tar.bz2 && \
    ln -s /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/share/phantomjs && \
    ln -s /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/bin/phantomjs && \
    ln -s /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/bin/phantomjs

RUN apt-get remove -y python-requests && apt-get install -y python-pip && pip install --upgrade pip

RUN phantomjs -v

RUN pip install -r requirements.txt && pip install --upgrade requests

ENTRYPOINT [ "python" ]
