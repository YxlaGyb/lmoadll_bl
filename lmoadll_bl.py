# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0

import os
from quart import Quart
from magic import Init_module
from dotenv import load_dotenv
from magic.middleware.response import ResponseManager, APIException

_ = load_dotenv()
app = Quart(__name__)
app.config["DEBUG"] = os.getenv("debug", "False").lower() in ("true", "1", "t")
app.json.sort_keys = False # pyright: ignore[reportAttributeAccessIssue]
ResponseManager(app)

async def init_app():
    await Init_module(app)

@app.get("/")
async def root():
    return {"Status": "OK"}
