"""prm Package Web Service API - Web server

Implements the Web servivce API as documented in doc/api/v1/prm-pckgsrv.yaml.

The online documentation is available at:
http://cds-dc.cims.nyu.edu/prm/package-server/
"""
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS
import os
import yaml

from prmpckgsrv.api import PrmPackageServer
import prmpckgsrv.const as const


# -----------------------------------------------------------------------------
#
# App Configuration
#
# -----------------------------------------------------------------------------

"""Read configuration parameter from a config file. The configuration file is
expected to be in YAML format containing a list 'properties' of {key, value}
pairs. Attempts to read the file specified in the environment variable
PRMPCKGSRV_CONFIG first. If the variable is not set (or if the specified file
does not exist) an attempt is made to read file config.yaml in the current
working directory. For all parameter that are not found in a config file the
default values (as defined below) are used.

These are the valid parameter keys:

- server.apppath : Application path part of the Url to access the app
- server.url : Base Url of the server where the app is running
- server.port : Port the server is running on
- server.logdir : Path to the log file directory

- app.name : Application (short) name for the service description
- app.debug : Flag to switch debugging on/off

- api.doc : Url for API documentation

- download.urlprefix: Url prefix for modules that have download task. In modules
  specifications all path expressions are expected to be relative to the
  packages directory of the file server that serves the files.

- package.index: File (in Yaml format) that contains the list of available
  packages on the server.
"""
# Set default configuration parameter
config = dict(const.DEFAULT_CONFIG)
config_file = os.getenv(const.ENV_CONFIG)
obj = None
if not config_file is None and os.path.isfile(config_file):
    with open(config_file, 'r') as f:
        obj = yaml.load(f.read())
elif os.path.isfile('./config.yaml'):
    with open('./config.yaml', 'r') as f:
        obj = yaml.load(f.read())
# Overwrite default configuration values if obj is not None
if not obj is None:
    for prop in  obj['properties']:
        config[prop['key']] = prop['value']


# ------------------------------------------------------------------------------
# Initialization
# ------------------------------------------------------------------------------

# Create the app and enable cross-origin resource sharing
app = Flask(__name__)
app.config['APPLICATION_ROOT'] = config[const.SERVER_APP_PATH]
app.config['DEBUG'] = config[const.APP_DEBUG]
CORS(app)

api = PrmPackageServer(config)


# ------------------------------------------------------------------------------
#
# Routes
#
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Service
# ------------------------------------------------------------------------------
@app.route('/')
def service_overview():
    """Retrieve essential information about the web service including relevant
    links to access resources and interact with the service.
    """
    return jsonify(api.service_overview())


# ------------------------------------------------------------------------------
# Packages
# ------------------------------------------------------------------------------
@app.route('/packages')
def list_packages():
    """Get a listing of packages that are available on the server."""
    return jsonify(api.list_packages())


@app.route('/packages/<string:package_query>')
def get_package_modules(package_query):
    """Retrieve descriptors for all modules that match the given package query.
    Queries are path expressions (using '.' as path delimiter) starting with
    a package name."""
    result = api.get_package_modules(package_query)
    if not result is None:
        return jsonify(result)
    raise ResourceNotFound('unknown package or module \'' + package_query + '\'')


# ------------------------------------------------------------------------------
#
# Exceptions
#
# ------------------------------------------------------------------------------

class ServerRequestException(Exception):
    """Base class for API exceptions."""
    def __init__(self, message, status_code):
        """Initialize error message and status code.

        Parameters
        ----------
        message : string
            Error message.
        status_code : int
            Http status code.
        """
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        """Dictionary representation of the exception.

        Returns
        -------
        Dictionary
        """
        return {'message' : self.message}


class ResourceNotFound(ServerRequestException):
    """Exception for file not found situations that have status code 404."""
    def __init__(self, message):
        """Initialize the message and status code (404) of super class.

        Parameters
        ----------
        message : string
            Error message.
        """
        super(ResourceNotFound, self).__init__(message, 404)


# ------------------------------------------------------------------------------
#
# Error Handler
#
# ------------------------------------------------------------------------------

@app.errorhandler(ServerRequestException)
def invalid_request_or_resource_not_found(error):
    """JSON response handler for invalid requests or requests that access
    unknown resources.

    Parameters
    ----------
    error : Exception
        Exception thrown by request Handler

    Returns
    -------
    Http response
    """
    app.logger.error(error.message)
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(500)
def internal_error(exception):
    """Exception handler that logs exceptions."""
    app.logger.error(exception)
    return make_response(jsonify({'error': str(exception)}), 500)


# ------------------------------------------------------------------------------
#
# Main
#
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    # Relevant documents:
    # http://werkzeug.pocoo.org/docs/middlewares/
    # http://flask.pocoo.org/docs/patterns/appdispatch/
    from werkzeug.serving import run_simple
    from werkzeug.wsgi import DispatcherMiddleware
    # Switch logging on if log directory is defined
    if 'server.logdir' in config:
        import logging
        from logging.handlers import RotatingFileHandler
        log_dir = os.path.abspath(config['server.logdir'])
        # Create the directory if it does not exist
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'vizier-api.log'),
            maxBytes=1024 * 1024 * 100,
            backupCount=20
        )
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        app.logger.addHandler(file_handler)
    # Load a dummy app at the root URL to give 404 errors.
    # Serve app at APPLICATION_ROOT for localhost development.
    application = DispatcherMiddleware(Flask('dummy_app'), {
        app.config['APPLICATION_ROOT']: app,
    })
    run_simple(
        '0.0.0.0',
        config[const.SERVER_PORT],
        application,
        use_reloader=config[const.APP_DEBUG]
    )
