import subprocess
import os
import logging
import shlex
import time

import hashlib

from krillbuild.language_loader import KrillLanguages
from krillbuild.project import KrillProject
from krillbuild.runner import get_runner

logger = logging.getLogger('krillbuild')

class KrillCompile():

    def __init__(self):
        self._runner = get_runner()

    def compile(self, krill_proj, language, options):
        lang_plugin = krill_proj.get_language(language)
        krill_proj.run_build_command(language, options)

            