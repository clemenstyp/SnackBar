#!/bin/bash
echo "--- install requirements ---"
pip3 install --upgrade -r requirements.txt
echo "--- Start migration ---"
python3 manage.py db init
python3 manage.py db migrate
python3 manage.py db upgrade

echo "--- finished migration ---"
