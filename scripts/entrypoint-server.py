#!/usr/bin/env python3

import os
import sys
import waitress

sys.path.append('.')
from maddie.wsgi import application
waitress.serve(application, port=int(os.getenv('PORT', '8080')))
