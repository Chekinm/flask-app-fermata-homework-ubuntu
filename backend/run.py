"""
Flask Application Launcher

This script serves as the entry point for running the Flask application.

To run the Flask application:
- Ensure that you have set the necessary configurations in 'config.config'.
- set FLASK_APP environment variable to run.py
    export FLASK_APP=run.py
- run flask with
    flask run

"""


from app import app
from config.config import FLASK_DEBUG

if __name__ == "main":
    app.run(debug=FLASK_DEBUG)
