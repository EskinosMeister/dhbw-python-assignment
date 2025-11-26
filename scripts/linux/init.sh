#!/bin/bash
pip install -r requirements.txt

python ../../database/reset_db.py
python ../../database/db_init.py