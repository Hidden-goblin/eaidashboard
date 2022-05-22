# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from fastapi.templating import Jinja2Templates
from dotenv import dotenv_values
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))

config = {**dotenv_values(".env"),
          **os.environ}

# base_url = f"{config['BACKEND']}/api/"
# raw_url = f"{config['BACKEND']}"

mongo_string = (f"mongodb://{config['MONGO_USR']}:{config['MONGO_PWD']}"
                f"@{config['MONGO_URL']}:{config['MONGO_PORT']}/")  # To variabilize
date_format = "%Y-%m-%d %H:%M"
