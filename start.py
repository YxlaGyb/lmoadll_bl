# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0

import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from lmoadll_bl import app, init_app

asyncio.run(init_app())
asyncio.run(serve(app, Config()))
