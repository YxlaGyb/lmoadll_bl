from quart import Blueprint
from magic.api.PluginApi import plugins

bp = Blueprint('plugins', __name__, url_prefix='/api/plugin')
bp.add_url_rule('/plugins', view_func=plugins.get_plugins, methods=['GET'])
bp.add_url_rule('/plugins/<plugin_name>', view_func=plugins.get_plugins, methods=['POST'])
bp.add_url_rule('/plugins/<plugin_name>', view_func=plugins.get_plugins, methods=['DELETE'])
bp.add_url_rule('/plugins/hooks', view_func=plugins.get_plugins, methods=['GET'])
