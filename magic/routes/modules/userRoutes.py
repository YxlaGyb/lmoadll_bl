from quart import Blueprint
from magic.api.auth import auth

bp = Blueprint('auth', __name__, url_prefix='/api/auth')
bp.add_url_rule('/login', view_func=auth.login_api, methods=['POST'])
bp.add_url_rule('/logout', view_func=auth.logout, methods=['POST'])
bp.add_url_rule('/user', view_func=auth.user_api, methods=['GET'])
bp.add_url_rule('/register', view_func=auth.register_api, methods=['POST'])
bp.add_url_rule('/email/code/register', view_func=auth.send_email_code_register_api, methods=['POST'])
bp.add_url_rule('/user/userInfoEdit', view_func=auth.user_info_edit_api, methods=['POST'])
