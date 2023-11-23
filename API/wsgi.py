"""
Archivo para iniciar el servidor de Flask.
Requerido por Gunicorn.
"""
import logging
from main import app

if __name__ == "__main__":
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    app.logger.info('Init server!')
    app.run()
