import os
import importlib

class KrillDevEnvs():

    def __init__(self):
        devenv_list = os.listdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "devenv"))

        self._devenvs = []

        for item in devenv_list:
            if item != "__init__.py" and item != "base.py" and  item.endswith(".py"):
                devenv_short = item.replace(".py", "")
                temp_mod = importlib.import_module("krillbuild.devenv." + devenv_short)
                for mod_item in dir(temp_mod):
                    if mod_item == "KrillPlugin":
                        continue
                    if "Plugin" in mod_item:
                        new_plugin = getattr(temp_mod, mod_item)()
                        new_plugin.shortname = devenv_short
                        self._devenvs.append(new_plugin)

    def list_devenvs(self):
        return self._devenvs
    
    def get_devenv(self, devenv):
        for plugin in self._devenvs:
            if plugin.shortname == devenv:
                return plugin
        raise ValueError(f"Devenv {devenv} not found")
