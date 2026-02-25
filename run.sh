#!/usr/bin/env bash
source /home/serv/.venvs/flask/bin/activate
python3 fileserver_flask.py --port 8080 --directory / 
