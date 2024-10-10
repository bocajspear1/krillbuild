import os
import importlib

class KrillCompilers():

    def __init__(self):
        compiler_list = os.listdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "compilers"))

        self._compilers = []

        for item in compiler_list:
            if item != "__init__.py" and item != "base.py" and  item.endswith(".py"):
                lang_short = item.replace(".py", "")
                temp_mod = importlib.import_module("krillbuild.compilers." + lang_short)
                for mod_item in dir(temp_mod):
                    if mod_item == "KrillPlugin":
                        continue
                    if "Plugin" in mod_item:
                        new_plugin = getattr(temp_mod, mod_item)()
                        self._compilers.append(new_plugin)
    
    def get_compiler(self, compiler):
        for plugin in self._compilers:
            if plugin.COMPILER_NAME == compiler:
                return plugin
        raise ValueError(f"Compiler {compiler} not found")