# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

import os
from fastapi.templating import Jinja2Templates
from dotenv import dotenv_values
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))

config = {**dotenv_values(".env"),
          **os.environ}


mongo_string = (f"mongodb://{config['MONGO_USR']}:{config['MONGO_PWD']}"
                f"@{config['MONGO_URL']}:{config['MONGO_PORT']}/")
date_format = "%Y-%m-%d %H:%M"

postgre_string = (f"postgresql://{config['PG_USR']}:{config['PG_PWD']}@"
                  f"{config['PG_URL']}:{config['PG_PORT']}/{config['PG_DB']}")


postgre_setting_string = (f"postgresql://{config['PG_USR']}:{config['PG_PWD']}@"
                          f"{config['PG_URL']}:{config['PG_PORT']}/postgres")


SECRET_KEY = None
PUBLIC_KEY = None
ALGORITHM = None
