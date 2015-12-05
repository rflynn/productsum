#!/bin/bash

source venv/bin/activate

set -v

while [ 1 ]
do
    AWS_ACCESS_KEY_ID=AKIAIJSFBGWDARVXQBSA \
    AWS_SECRET_ACCESS_KEY=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 \
    AWS_DEFAULT_REGION=us-east-1 \
    PYTHONPATH=. \
    python spider_frontend/spider_dynamo.py $@;
    sleep 30
done

