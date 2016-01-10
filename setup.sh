#!/bin/sh
rm -fr venv
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
