import os
import importlib

class KrillMods():

    def __init__(self):
        mod_list = os.listdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "mods"))

        self._mods = []
        

        for item in mod_list:
            if item != "__init__.py" and item != "base.py" and item.endswith(".py"):
                mod_short = item.replace(".py", "")
                temp_mod = importlib.import_module("krillbuild.mods." + mod_short)
                for mod_item in dir(temp_mod):
                    if mod_item == "KrillPlugin":
                        continue
                    if "Plugin" in mod_item:
                        new_plugin = getattr(temp_mod, mod_item)()
                        new_plugin.shortname = mod_short
                        self._mods.append(new_plugin)

    def list_mods(self):
        return self._mods
    
    def get_mod(self, mod_name):
        for plugin in self._mods:
            if plugin.shortname == mod_name:
                return plugin
        raise ValueError(f"Mod {mod_name} not found")