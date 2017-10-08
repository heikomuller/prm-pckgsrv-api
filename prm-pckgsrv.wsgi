activate_this = '/var/www/prm/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import os
import sys
sys.path.insert(0, '/var/www/prm/src')

os.environ['PRMPCKGSRV_CONFIG'] = '/var/www/prm/config.yaml'

from prmpckgsrv.server import app as application
application.secret_key = 'Add your secret key'

