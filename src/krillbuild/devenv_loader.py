import os
import sys
import importlib


class KrillDevEnvs():

    def __init__(self):
        if 'KRILL_PROJECT' in os.environ:
            self._project_path = os.path.join(os.environ['KRILL_PROJECT'], ".krill")
        else:
            self._project_path = None

        devenv_list = os.listdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "devenv"))

        self._devenvs = []

        for item in devenv_list:
            if item != "__init__.py" and item != "base.py" and  item.endswith(".py"):
                devenv_short = item.replace(".py", "")
                temp_mod = importlib.import_module("krillbuild.devenv." + devenv_short)
                self._load_from_module(devenv_short, temp_mod)

        if self._project_path is not None:
            project_devenv_path = os.path.join(self._project_path, "devenv")
            if os.path.exists(project_devenv_path):
                proj_devenv_list = os.listdir(project_devenv_path)
                for item in proj_devenv_list:
                    if item != "__init__.py" and item.endswith(".py"):
                        devenv_short = item.replace(".py", "")
                        self.load_external(devenv_short, os.path.join(project_devenv_path, item))

    def _load_from_module(self, devenv_short, module):
        for mod_item in dir(module):
            if mod_item == "KrillPlugin":
                continue
            if "Plugin" in mod_item:
                new_plugin = getattr(module, mod_item)()
                new_plugin.shortname = devenv_short
                self._devenvs.append(new_plugin)

    def list_devenvs(self):
        return self._devenvs
    
    def get_devenv(self, devenv):
        for plugin in self._devenvs:
            if plugin.shortname == devenv:
                return plugin
        raise ValueError(f"Devenv {devenv} not found")
    
    def load_external(self, name, path):
        full_module_name = "custom." + name
        spec = importlib.util.spec_from_file_location(full_module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[full_module_name] = module
        spec.loader.exec_module(module)
        self._load_from_module(name, module)
        
        if self._project_path is not None:
            project_devenv_path = os.path.join(self._project_path, "devenv")
            if not os.path.exists(project_devenv_path):
                os.mkdir(project_devenv_path)
            link_path = os.path.join(project_devenv_path, os.path.basename(path))
            if not os.path.exists(link_path):
                os.link(path, link_path)
