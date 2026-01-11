from quart import Blueprint
from magic.asses import asses

bp = Blueprint('asses', __name__, url_prefix='/asses')
bp.add_url_rule('/admin/<path:filename>', view_func=asses.admin_assess_css)
bp.add_url_rule('/install/<path:filename>', view_func=asses.install_assess)
