import os
import importlib

class KrillLanguages():

    def __init__(self):
        language_list = os.listdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "languages"))

        self._language_mods = []

        for item in language_list:
            if item != "__init__.py" and item != "base.py" and  item.endswith(".py"):
                lang_short = item.replace(".py", "")
                temp_mod = importlib.import_module("krillbuild.languages." + lang_short)
                for mod_item in dir(temp_mod):
                    if mod_item == "KrillPlugin":
                        continue
                    if "Plugin" in mod_item:
                        new_plugin = getattr(temp_mod, mod_item)()
                        new_plugin.shortname = lang_short
                        self._language_mods.append(new_plugin)
    
    def get_language(self, language):
        for plugin in self._language_mods:
            if plugin.shortname == language:
                return plugin
        raise ValueError(f"Language {language} not found")