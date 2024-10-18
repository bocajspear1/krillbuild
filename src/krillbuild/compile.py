import subprocess
import os
import logging
import shlex
import configparser
import copy
from urllib.parse import urlparse, unquote

import requests

import hashlib

from krillbuild.runner import get_runner
from krillbuild.util import is_basic_string

logger = logging.getLogger('krillbuild')


class KrillBuildObject():
    def __init__(self, name, compiler, commands, static=True):
        print(name)
        self._name = is_basic_string(name)
        self._static = static
        self._compiler = is_basic_string(compiler)
        self._commands = commands

    @property
    def is_static(self):
        return self._static
    
    @property
    def name(self):
        return self._name
    
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

    

class KrillBuild():

    def __init__(self, config_path):
        self._config_path = config_path
        
        self._config = None
        self._devenv = None
        self._arch_list = []
        self._libraries = []
        self._main = None

    @property
    def devenv(self):
        return copy.deepcopy(self._devenv)

    @property
    def architectures(self):
        return copy.deepcopy(self._arch_list)
    
    @property
    def libraries(self):
        return copy.deepcopy(self._libraries)
    
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
            print(self._config)

            krill_section = self._config['krill']
            if 'archlist' not in krill_section:
                raise ValueError("'archlist' item not found")
            self._arch_list = krill_section['archlist'].split(",")
            self._devenv = krill_section['devenv']

            for section in self._config:
                section_item = self._config[section]
                if section.startswith("lib."):
                    new_lib = KrillLibrary(section[4:], section_item['source'], section_item['compiler'], section_item['commands'].strip())
                    self._libraries.append(new_lib)
                elif section == "main":
                    self._main = KrillBuildObject("main", section_item['compiler'], section_item['commands'].strip())
        
        return True

    def check_libraries(self):
        pass


            