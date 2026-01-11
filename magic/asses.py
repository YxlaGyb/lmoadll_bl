from quart import send_from_directory

class asses:
    @staticmethod
    def admin_assess_css(filename):
        return send_from_directory('admin/asses/', filename)

    @staticmethod
    def install_assess(filename):
        return send_from_directory('admin/asses/', filename)
