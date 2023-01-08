# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging
from os import makedirs

import uvicorn

if __name__ == "__main__":
    makedirs("app/static", exist_ok=True)
    uvicorn.run("app.api:app", host="0.0.0.0", port=8081, reload=True)
