#!/bin/bash

pip install -r requirements.txt

python reset_db.py
python app.py