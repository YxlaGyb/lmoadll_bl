# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
from quart import Blueprint
from magic.api.AdminEndpoints import admin_bp


api_bp = Blueprint('api', __name__, url_prefix='/api')
api_bp.register_blueprint(admin_bp, url_prefix='/admin')
