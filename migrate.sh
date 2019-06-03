#!/bin/bash
echo "--- Start migration ---"
python3 manage.py db init
python3 manage.py db migrate
python3 manage.py db upgrade

echo "--- finished migration ---"
