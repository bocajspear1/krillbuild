import subprocess
import os
import logging
import shlex
import configparser
import copy
from urllib.parse import urlparse, unquote
from string import Template


import requests

import hashlib

from krillbuild.runner import get_runner
from krillbuild.util import is_basic_string

logger = logging.getLogger('krillbuild')


class KrillBuildMain():

    def __init__(self, main_obj):
        self._variations = []
        self._main_obj = main_obj

    def add_variation(self, name, archlist, args):
        self._variations.append({
            "name": name,
            'archlist': archlist,
            'args': args
        })

    def variations(self, arch):
        if len(self._variations) == 0:
            return [self._main_obj]
        
        return_list = []
        for variation in self._variations:
            if arch in variation['archlist']:
                
                command_list = self._main_obj.commands
                new_commands = []
                for arg in variation['args']:
                    found = False
                    arg_val = f"%{arg}%"
                    for i in range(len(command_list)):
                        if arg_val in command_list[i]:
                            found = True
                            new_command = command_list[i].replace(arg_val, variation['args'][arg])
                            new_command = new_command.replace("$KRILL_VARIATION", variation['name'])
                            new_commands.append(new_command)
                    if not found:
                        raise ValueError("Arg %s not found in any command", arg_val)

                new_obj = KrillBuildObject(self._main_obj.name, self._main_obj.compiler, new_commands, variation=variation['name'])
                return_list.append(new_obj)

            else:
                logger.debug("Ignoring variation %s, not in archlist", variation['name'])

        return return_list  

class KrillBuildObject():
    def __init__(self, name, compiler, commands, static=True, variation=None):
        self._name = is_basic_string(name)
        self._static = static
        self._compiler = is_basic_string(compiler)
        self._commands = commands
        self._variation = variation

    @property
    def is_static(self):
        return self._static
    
    @property
    def name(self):
        return self._name
    
    @property
    def variation(self):
        return self._variation
    
    @property
    def commands(self):
        return self._commands
    
    @property
    def compiler(self):
        return self._compiler
   


class KrillLibrary(KrillBuildObject):

    def __init__(self, name, source, compiler, commands, static=True):
        super().__init__(name, compiler, commands, static=static)
        self._source = source
        
    def exists(self, lib_dir):
        return os.path.exists(os.path.join(lib_dir, f"lib{self.name}.a"))
    
    def download(self, cache_dir):
        source_url = urlparse(self._source)
        file_name = os.path.basename(source_url.path)
        final_path = os.path.join(cache_dir, file_name)
        if not os.path.exists(final_path):
            logger.info("Downloading %s to %s", self._source, final_path)
            with open(final_path, "wb") as download_file:
                resp = requests.get(self._source, allow_redirects=True)
                download_file.write(resp.content)
        else:
            logger.info("Using cached file %s", final_path)

        return final_path

class KrillBuildMod():

    def __init__(self, mod_name, tool, infile, outfile, options, archlist=None):
        self._name = mod_name
        self._tool = tool
        self._infile = infile
        self._outfile = outfile
        self._options = options
        self._archlist = archlist

    @property
    def name(self):
        return self._name

    @property
    def tool(self):
        return self._tool
    
    @property
    def archlist(self):
        return self._archlist
    
    def infile(self, env_vars):
        return Template(self._infile).safe_substitute(env_vars)
    
    def outfile(self, env_vars):
        return Template(self._outfile).safe_substitute(env_vars)
    
    @property
    def options(self):
        return self._options
    
class KrillBuild():

    def __init__(self, config_path):
        self._config_path = config_path
        
        self._config = None
        self._devenv = None
        self._devenv_path = None
        self._arch_list = []
        self._libraries = []
        self._mods = []
        self._main = None

    @property
    def devenv(self):
        return copy.deepcopy(self._devenv)
    
    @property
    def devenv_path(self):
        return self._devenv_path

    @property
    def architectures(self):
        return copy.deepcopy(self._arch_list)
    
    @property
    def libraries(self):
        return copy.deepcopy(self._libraries)
    
    @property
    def mods(self):
        return copy.deepcopy(self._mods)
    
    @property
    def main(self):
        return self._main
    
    def load(self):
        if not os.path.exists(self._config_path):
            logger.error("krill.ini does not exist in %s", self._project.path)
            return False

        parser = configparser.ConfigParser()

        with open(self._config_path, "r") as config_file:
            parser.read_file(config_file)
            self._config = parser._sections

            krill_section = self._config['krill']
            if 'archlist' not in krill_section:
                raise ValueError("'archlist' item not found")
            self._arch_list = krill_section['archlist'].split(",")
            self._devenv = krill_section['devenv']
            if 'path' in krill_section:
                self._devenv_path = krill_section['path']

            for section in self._config:
                section_item = self._config[section]
                if section.startswith("lib."):
                    new_lib = KrillLibrary(section[4:], section_item['source'], section_item['compiler'], section_item['commands'].strip())
                    self._libraries.append(new_lib)
                elif section.startswith("mod."):
                    mod_id = section[4:]
                    mod_split = mod_id.split(".")
                    
                    mod_name = mod_split[0]
                    new_mod = None
                    if 'archlist' in section_item:
                        new_mod = KrillBuildMod(mod_name, mod_split[1], section_item['infile'], section_item['outfile'], 
                                                section_item['options'], archlist=section_item['archlist'].split(","))
                    else:
                        new_mod = KrillBuildMod(mod_name, mod_split[1], section_item['infile'], section_item['outfile'], 
                                                section_item['options'])
                        
                    if 'after' in section_item:
                        if len(self._mods) == 0:
                            raise ValueError("Cannot have 'after' in first mod")
                        mod_found = False
                        search_mod = section_item['after'][4:]
                        for i in range(len(self._mods)):
                            mod_map = self._mods[i]
                            if search_mod in mod_map:
                                mod_found = True
                                if i == len(self._mods)-1:
                                    self._mods.append({
                                        mod_id: new_mod
                                    })
                                else:
                                    self._mods[i+1][mod_id] = new_mod
                            if not mod_found:
                                raise ValueError(f"Mod {search_mod} not found for 'after' setting in mod {mod_id}")
                    else:
                        self._mods.append({
                            mod_id: new_mod
                        })
                elif section == "main":
                    self._main = KrillBuildMain(KrillBuildObject("main", section_item['compiler'], section_item['commands'].strip().split("\n")))
                elif section.startswith("main."):
                    var_archlist = []
                    if 'archlist' in section_item:
                        var_archlist = section_item['archlist'].split(',')

                    args_map = {}

                    for item_name in section_item:
                        if item_name not in ('archlist',):
                            args_map[item_name.upper()] = section_item[item_name]
                    self._main.add_variation( section[5:], var_archlist, args_map)
                
        
        return True

    def check_libraries(self):
        pass


            