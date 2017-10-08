"""prm Package Web Service API - Constants

Collection of constants that are used to control configuration of the Web
service API.
"""

"""Environment variable containing path to config file."""
ENV_CONFIG = 'PRMPCKGSRV_CONFIG'


"""Configuration keys"""
API_DOC = 'api.doc'

APP_NAME = 'app.name'
APP_DEBUG = 'app.debug'

DOWNLOAD_URLPREFIX = 'download.urlprefix'

PACKAGE_INDEXFILE = 'package.index'

SERVER_APP_PATH = 'server.apppath'
SERVER_URL = 'server.url'
SERVER_PORT = 'server.port'
SERVER_LOG_DIR = 'server.logdir'


"""Default Web Service configuration."""
DEFAULT_CONFIG = {
    SERVER_APP_PATH : '/package-server/api/v1',
    SERVER_URL : 'http://localhost',
    SERVER_PORT : 5000,
    API_DOC : 'http://cds-dc.cims.nyu.edu/prm/package-server/',
    APP_NAME : 'prm - Project Repository Manager',
    APP_DEBUG : True,
    DOWNLOAD_URLPREFIX: 'http://cds-dc.cims.nyu.edu/prm/packages',
    PACKAGE_INDEXFILE: './.packages/index.yaml'
}
