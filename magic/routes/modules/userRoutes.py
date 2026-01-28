from quart import Blueprint
from magic.controller.userController import UserController

bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')
bp.add_url_rule('/login', view_func=UserController.login, methods=['POST'])
bp.add_url_rule('/regter', view_func=UserController.register, methods=['POST'])
bp.add_url_rule('/email/code/regter', view_func=UserController.sendEmailCodeRegister, methods=['POST'])
bp.add_url_rule('/user/profile', view_func=UserController.getUserProfile, methods=['GET'])
bp.add_url_rule('/users', view_func=UserController.getUserByUsername, methods=['GET'])
bp.add_url_rule('/users/cre', view_func=UserController.createUser, methods=['POST'])
bp.add_url_rule('/users/upd', view_func=UserController.updateUser, methods=['POST'])
bp.add_url_rule('/users/del', view_func=UserController.deleteUser, methods=['POST'])
