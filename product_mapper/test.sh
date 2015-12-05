#!/bin/bash

source ../venv/bin/activate

err=0

for p in *.py
do
    printf '%-20s ' $p
    python $p >/dev/null 2>&1
    e=$?
    printf '%d\n' $e
    test -z $e || err=1
done

test -z $err || exit 1

