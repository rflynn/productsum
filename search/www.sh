#!/bin/bash

source ../venv/bin/activate

while true
do
    PYTHONPATH=.. python www_products.py
    sleep 3
done

