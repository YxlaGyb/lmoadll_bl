import os
import importlib
import glob

async def combineRoutes(app):
    modules_dir = os.path.join('magic', 'routes', 'modules')
    module_files = glob.glob(f"{modules_dir}/*.py")
    for file in module_files:
        module_name = os.path.basename(file)[:-3]
        if module_name.startswith('_'):
            continue
        module = importlib.import_module(f"magic.routes.modules.{module_name}")
        for attr in ['bp']:
            if hasattr(module, attr):
                app.register_blueprint(getattr(module, attr))
                break
