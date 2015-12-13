#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=4 et:

from flask import Flask, render_template, redirect
import time


app = Flask(__name__)

@app.route('/')
def index():
    return redirect('/query')

@app.route('/query')
def testcases():
    t = time.time()
    return render_template('query.html',
                           t=round(time.time()-t, 1))

if __name__ == '__main__':
    app.run(host='0.0.0.0',
            port=9998,
            debug=True)

