#!/bin/bash

set -v
set -e

sudo apt-get update

# libs
sudo apt-get install -y postgresql-9.3
sudo apt-get install -y postgresql-server-dev-9.3 # psycopg2

# we need the postgresql packages, but we don't want the server
# XXX: there *has* to be a smarter way of doing this...
sudo /etc/init.d/postgresql stop
sudo update-rc.d postgresql disable

#sudo apt-get install -y rabbitmq-server
#sudo apt-get install -y librabbitmq-dev
sudo apt-get install -y libyaml-dev
sudo apt-get install -y libxml2-dev # scrapy
sudo apt-get install -y libxslt1-dev # needed for lxml?
sudo apt-get install -y libffi-dev

# python
sudo apt-get install -y --force-yes python-dev
sudo apt-get install -y --force-yes python-cffi
sudo apt-get install -y python-pip
sudo apt-get install -y python-virtualenv
# XXX: NOTE: pip install lxml compiles libxml, which is monstrous compile that fails on small machines,
# so we install the binary instead
sudo apt-get install -y python-lxml # pip lxml doesn't always work...

# spider...
sudo apt-get install -y --force-yes build-essential chrpath libssl-dev libxft-dev
sudo apt-get install -y libfreetype6 libfreetype6-dev
sudo apt-get install -y libfontconfig1 libfontconfig1-dev
sudo apt-get install -y --force-yes phantomjs
sudo apt-get install -y --force-yes xvfb
sudo apt-get install -y --force-yes chromium-browser
sudo apt-get install -y --force-yes chromium-chromedriver
sudo apt-get install -y --force-yes firefox

# graphviz
sudo apt-get install -y graphviz libgraphviz-dev pkg-config

# install mosh
sudo apt-get install -y python-software-properties
sudo add-apt-repository -y ppa:keithw/mosh
sudo apt-get update
sudo apt-get -y install -y mosh

# misc
sudo apt-get install -y jq

# set up python virtualenv
test -d venv || virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
pip freeze > requirements.txt  # save results in case we missed dependencies

# run NLTK download step...
python -m nltk.downloader punkt

# custom pygraphviz wtf
# ref: https://github.com/pygraphviz/pygraphviz/issues/71
pip install pygraphviz --install-option="--include-path=/usr/include/graphviz" --install-option="--library-path=/usr/lib/graphviz/"

