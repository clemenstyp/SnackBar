# coding: utf-8
import argparse
import logging
import os
import secrets
from logging.handlers import SMTPHandler

from werkzeug.middleware.dispatcher import DispatcherMiddleware

from Snackbar import app
from Snackbar.Adminpage import setup_admin
from Snackbar.Frontpage import setup_frontpage
from Snackbar.Helper.Autoreminder import setup_schedule, stop_schedule, start_schedule
from Snackbar.Helper.Database import database_exist, set_default_settings, build_sample_db, settings_for


class Options:
    pass


def simple(env, resp):
    resp('301 Moved Permanently', [('Location', options.url_prefix)])
    return [b'']
    # resp(b'200 OK', [(b'Content-Type', b'text/plain')])
    # return [b'You have to call the url_prefix']


def load_args_options():
    global options
    """
    Parses command-line flags to configure the app.
    """
    # Set up the command-line options
    parser = argparse.ArgumentParser(prog='SnackBar')

    parser.add_argument("-H", "--host",
                        help=f"Hostname of the Flask app [default {options.host}]",
                        default=options.host)
    parser.add_argument("-P", "--port",
                        help=f"Port for the Flask app [default {options.port}]",
                        default=options.port)

    parser.add_argument("-U", "--url_prefix",
                        help=f"Url Prefix for the Flask app [default {options.url_prefix}]",
                        default=options.url_prefix)

    # Two options useful for debugging purposes, but
    # a bit dangerous so not exposed in the help message.
    parser.add_argument("-d", "--debug",
                        action="store_true", dest="debug",
                        help="enable debug")

    parser.parse_args(namespace=options)


def get_default_options(default_host="0.0.0.0", default_port="5000", default_url_prefix=""):
    default_options = Options()

    if host := os.getenv("SNACKBAR_HOST"):
        default_options.host = host
    else:
        default_options.host = default_host

    if port := os.getenv("SNACKBAR_PORT"):
        default_options.port = port
    else:
        default_options.port = default_port

    if url_prefix := os.getenv("SNACKBAR_URL_PREFIX"):
        default_options.url_prefix = url_prefix
    else:
        default_options.url_prefix = default_url_prefix

    if os.getenv("SNACKBAR_DEBUG").lower() == 'true':
        default_options.debug = True
    else:
        default_options.debug = False

    if secret_key := os.getenv("SNACKBAR_SECRETKEY"):
        default_options.secret_key = secret_key
    else:
        default_options.secret_key = secrets.token_hex()

    if mail_errors_to := os.getenv("SNACKBAR_MAIL_ERRORS_TO"):
        default_options.mail_errors_to = mail_errors_to
    else:
        default_options.mail_errors_to = False

    return default_options


def init_app():
    global options
    app.wsgi_app = DispatcherMiddleware(simple, {options.url_prefix: app.wsgi_app})
    app.config["APPLICATION_ROOT"] = options.url_prefix
    app.config['SECRET_KEY'] = f"{options.secret_key}_{options.url_prefix}"
    app.config['DEBUG'] = options.debug

    if database_exist() is False:
        build_sample_db()
    set_default_settings()

    # Email Errors to Admins
    if options.mail_errors_to:
        mail_handler = SMTPHandler(
            mailhost=settings_for('mailServer'),
            fromaddr=settings_for('mailSender'),
            toaddrs=[options.mail_errors_to],
            subject=f"Application Error on Snackbar {options.url_prefix}"
        )
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        app.logger.addHandler(mail_handler)

    if options.debug:
        logging.getLogger("werkzeug").setLevel(logging.DEBUG)
    else:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)

    setup_schedule()
    setup_admin(app)
    setup_frontpage()


options = get_default_options()

if __name__ == "__main__":
    load_args_options()
    init_app()
    start_schedule()
    app.run(debug=options.debug, host=options.host, port=int(options.port))
    stop_schedule()
