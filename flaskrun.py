import optparse
from werkzeug.serving import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import logging
import os
def simple(env, resp):
    resp(b'200 OK', [(b'Content-Type', b'text/plain')])
    return [b'You have to call the url_prefix']

def load_options(default_host="127.0.0.1",
             default_port="5000", url_prefix=""):
    """
    Parses command-line flags to configure the app.
    """

    # Set up the command-line options
    parser = optparse.OptionParser()
    parser.add_option("-H", "--host",
                      help="Hostname of the Flask app " +
                           "[default %s]" % default_host,
                      default=default_host)
    parser.add_option("-P", "--port",
                      help="Port for the Flask app " +
                           "[default %s]" % default_port,
                      default=default_port)

    parser.add_option("-U", "--url_prefix",
                      help="Url Prefix for the Flask app " +
                           "[default %s]" % url_prefix,
                      default=url_prefix)

    # Two options useful for debugging purposes, but
    # a bit dangerous so not exposed in the help message.
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug",
                      help=optparse.SUPPRESS_HELP)
    parser.add_option("-p", "--profile",
                      action="store_true", dest="profile",
                      help=optparse.SUPPRESS_HELP)

    options, _ = parser.parse_args()

    if host := os.getenv("SNACKBAR_HOST"):
        options.host = host
    if port := os.getenv("SNACKBAR_PORT"):
        options.port = port
    if url_prefix := os.getenv("SNACKBAR_URL_PREFIX"):
        options.url_prefix = url_prefix
    if os.getenv("SNACKBAR_DEBUG"):
        options.debug = True

    return options

def flaskrun(app, options=None):
    """
    Takes a flask.Flask instance and runs it.
    """

    # Set up the command-line options
    if options is None:
        options = load_options()

    if not options.debug:
        options.debug = False
    # If the User selects the profiling option, then we need
    # to do a little extra setup
    if options.profile:
        # noinspection PyPackageRequirements
        from werkzeug.contrib.profiler import ProfilerMiddleware

        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app,
                                          restrictions=[30])
        options.debug = True

    app.wsgi_app = DispatcherMiddleware(simple, {options.url_prefix: app.wsgi_app})

    app.config["APPLICATION_ROOT"] = options.url_prefix

    if not options.debug:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
    else:
        logging.getLogger("werkzeug").setLevel(logging.DEBUG)

    app.run(
        debug=options.debug,
        host=options.host,
        port=int(options.port)
    )
