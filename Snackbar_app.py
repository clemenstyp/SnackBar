# coding: utf-8
import argparse
import logging
import os
from logging.handlers import SMTPHandler

from werkzeug.middleware.dispatcher import DispatcherMiddleware

from Snackbar import app
from Snackbar.Adminpage import setup_admin
from Snackbar.Frontpage import setup_frontpage
from Snackbar.Helper.Autoreminder import setup_schedule, stop_schedule
from Snackbar.Helper.Database import database_exist, set_default_settings, build_sample_db, settings_for


def simple(env, resp):
    resp(b'200 OK', [(b'Content-Type', b'text/plain')])
    return [b'You have to call the url_prefix']


def load_args(default_host="127.0.0.1", default_port="5000", url_prefix=""):
    """
    Parses command-line flags to configure the app.
    """

    # Set up the command-line options
    parser = argparse.ArgumentParser(prog='SnackBar')

    parser.add_argument("-H", "--host",
                        help="Hostname of the Flask app " +
                        "[default %s]" % default_host,
                        default=default_host)
    parser.add_argument("-P", "--port",
                        help="Port for the Flask app " +
                        "[default %s]" % default_port,
                        default=default_port)

    parser.add_argument("-U", "--url_prefix",
                        help="Url Prefix for the Flask app " +
                        "[default %s]" % url_prefix,
                        default=url_prefix)

    # Two options useful for debugging purposes, but
    # a bit dangerous so not exposed in the help message.
    parser.add_argument("-d", "--debug",
                        action="store_true", dest="debug",
                        help="enable debug")
    parser.add_argument("-p", "--profile",
                        action="store_true", dest="profile",
                        help="")

    loaded_args = parser.parse_args()

    if host := os.getenv("SNACKBAR_HOST"):
        loaded_args.host = host
    if port := os.getenv("SNACKBAR_PORT"):
        loaded_args.port = port
    if url_prefix := os.getenv("SNACKBAR_URL_PREFIX"):
        loaded_args.url_prefix = url_prefix
    if os.getenv("SNACKBAR_DEBUG"):
        loaded_args.debug = True

    return loaded_args


def flaskrun(flask_app, args=None):
    """
  Takes a flask.Flask instance and runs it.
  """
    if args is None:
        args = load_args()

    if not args.debug:
        args.debug = False

        # If the User selects the profiling option, then we need
        # to do a little extra setup
    if args.profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        flask_app.config['PROFILE'] = True
        flask_app.wsgi_app = ProfilerMiddleware(flask_app.wsgi_app, restrictions=[30])
        args.debug = True

    flask_app.wsgi_app = DispatcherMiddleware(simple, {args.url_prefix: flask_app.wsgi_app})
    flask_app.config["APPLICATION_ROOT"] = args.url_prefix

    if not args.debug:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
    else:
        logging.getLogger("werkzeug").setLevel(logging.DEBUG)

    flask_app.run(debug=args.debug, host=args.host, port=int(args.port))


if __name__ == "__main__":
    setup_schedule()
    if database_exist() is False:
        build_sample_db()
    set_default_settings()

    flask_args = load_args()

    # Email Errors to Admins
    mail_handler = SMTPHandler(
        mailhost=settings_for('mailServer'),
        fromaddr=settings_for('mailSender'),
        toaddrs=['clemens.eyhoff@fit.fraunhofer.de'],
        subject='Application Error'
    )
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))

    if not flask_args.debug:
        app.logger.addHandler(mail_handler)

    setup_admin(app)
    setup_frontpage()

    app.config['SECRET_KEY'] = '123456790' + flask_args.url_prefix
    app.config["APPLICATION_ROOT"] = flask_args.url_prefix

    # app.run()
    # app.run(host='0.0.0.0', port=5000, debug=False)
    flaskrun(app, args=flask_args)
    stop_schedule()
