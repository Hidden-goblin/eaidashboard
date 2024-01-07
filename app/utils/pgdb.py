# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from psycopg_pool import ConnectionPool

from app.conf import config

pool = ConnectionPool(f"host={config['PG_URL']} port={config['PG_PORT']} user={config['PG_USR']}"
                      f" password={config['PG_PWD']} dbname={config['PG_DB']}", open=True, num_workers=6)
