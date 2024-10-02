import os
import subprocess
import hashlib
import logging
import time
import shlex
import stat
import sys

logger = logging.getLogger('krillbuild')

activate_script_sh="""
KRILL_ARCH='invalid'
if [ -z "$1" ]; then
    echo "Architecture must be set"
{arch_cond}
else
    echo "Invalid architecture"
fi

if [ "$KRILL_ARCH" != "invalid" ]; then
    export KRILL_PROJECT={project_path}
    export KRILL_INSTALL_DIR={project_path}/.krill/${{KRILL_ARCH}}
    export KRILL_ARCH
    mkdir -p {project_path}/.krill/${{KRILL_ARCH}}/lib
    mkdir -p {project_path}/.krill/${{KRILL_ARCH}}/bin
    mkdir -p {project_path}/.krill/${{KRILL_ARCH}}/include
    krillbuild project info
fi
"""

from krillbuild.runner import get_runner
from krillbuild.language_loader import KrillLanguages
from krillbuild.mod_loader import KrillMods
from krillbuild.architectures import ARCHITECTURE_LIST

class KrillProject():

    @classmethod
    def init(cls, project_path, dir_path=".krill"):
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
            os.mkdir(os.path.join(dir_path, "bin"))
            # os.mkdir(os.path.join(path, "bin"))
        activate_path = os.path.join(dir_path, "bin", "activate")
        with open(activate_path, "w") as activate_file:

            arch_cond = ""
            for arch in ARCHITECTURE_LIST:
                arch_cond += f"elif [ \"$1\" == \"{arch}\" ]; then\n"
                arch_cond += f"    KRILL_ARCH=$1\n"

            activate_file.write(activate_script_sh.format(project_path=project_path, arch_cond=arch_cond))
        os.chmod(activate_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IXOTH | stat.S_IROTH)
        
    @classmethod
    def get_project(cls):

        if 'KRILL_PROJECT' in os.environ:
            project_obj = cls(os.environ['KRILL_PROJECT'], os.getenv('KRILL_ARCH'))
            return project_obj
        else:
            return None
        
    def __init__(self, project_path, arch, temp=False):
        self._lang_loader = KrillLanguages()
        self._mod_loader = KrillMods()
        self._project_path = os.path.abspath(project_path)
        self._arch = arch
        self._temp = temp

    @property
    def project_path(self):
        return self._project_path
    
    @property
    def arch(self):
        return self._arch
    
    @property
    def temp(self):
        return self._temp

    def get_language(self, language):
        return self._lang_loader.get_language(language)
    
    def get_mod(self, modname):
        return self._mod_loader.get_mod(modname)
    
    def get_running_name(self, lang_shortname, arch):
        project_path_hash = hashlib.md5(self._project_path.encode()).hexdigest()
        return f"krill{project_path_hash}-{lang_shortname}.{arch}"
    
    def info(self):
        current_arch = self._arch
        project_path = self._project_path

        print(f"Project path: {project_path}")
        print(f"Current architecture: {current_arch}")
    
    def init_container(self, language, options):

        if self.temp:
            return
        
        lang_plugin = self.get_language(language)

        container, command, env_vars, new_options = lang_plugin.prepare_compile(self._arch, options)

        env_variables = []

        if env_vars is not None:
            for env_var_name in env_vars:
                env_variables.append(f"-e{env_var_name}={env_vars[env_var_name]}")

        print(container)

        running_name = self.get_running_name(lang_plugin.shortname, self._arch)

        runner = get_runner()

        inspect_command = [
            runner,
            "inspect",
            running_name
        ]

        logger.info("Inspecting for project container '%s' with %s", container, shlex.join(inspect_command))


        result = subprocess.run(inspect_command, capture_output=True)
        if result.returncode != 0:
            full_command = [
                runner,
                "run",
                "--rm",
                f"--name={running_name}", 
                f"-v{self._project_path}:/work"
            ]
            full_command += env_variables
            full_command += [
                container,
                "sh", "-c", "while [ 1 ]; do sleep 5; done"
            ]
            logger.info("Starting project container '%s' with %s", container, shlex.join(full_command))
            new_proc = subprocess.Popen(full_command)
            time.sleep(5)
            if new_proc.poll() != None:
                logger.error("Container failed to start!")
                logger.error("Output: %s", new_proc.stderr.read().decode())
                return
            else:
                logger.debug("Started building container")

    def stop_container(self, language, options):
        lang_plugin = self.get_language(language)
        running_name = self.get_running_name(lang_plugin.shortname,  self._arch)

        runner = get_runner()

        inspect_command = [
            runner,
            "inspect",
            running_name
        ]

        logger.info("Inspecting for project container with %s", shlex.join(inspect_command))


        result = subprocess.run(inspect_command, capture_output=True)
        if result.returncode == 0:
            full_command = [
                runner,
                "stop",
                running_name
            ]
            logger.info("Stopping project container with %s", shlex.join(full_command))
            new_proc = subprocess.run(full_command)



    def run_mod_command(self, mod, filename, options):
        mod_plugin = self.get_mod(mod)
        running_name = self.get_running_name(mod_plugin.shortname, self._arch)
        container, command, env_vars, new_options = mod_plugin.prepare_mod(self._arch, filename, list(options))

        env_variables = []

        if env_vars is not None:
            for env_var_name in env_vars:
                env_variables.append(f"-e{env_var_name}={env_vars[env_var_name]}")

        full_command = [
            get_runner(),
            "run",
            "-i",
            "--rm",
            f"-v{self._project_path}:/work",
        ]
        full_command += env_variables
        full_command += [
            container,
            command
        ]
        full_command += new_options

        logger.debug("Temp container command is: %s", shlex.join(full_command))

        result = subprocess.run(full_command)

    def run_build_command(self, language, options):
        lang_plugin = self.get_language(language)
        running_name = self.get_running_name(lang_plugin.shortname, self._arch)
        container, command, env_vars, new_options = lang_plugin.prepare_compile(self._arch, options)
        result = None

        if new_options is None:
            new_options = []
        else:
            new_options = list(new_options)

        for i in range(len(new_options)):
            if self._project_path in new_options[i]:
                new_options[i] = new_options[i].replace(self._project_path, "/work")

        if self._temp:

            env_variables = []

            
            if env_vars is not None:
                for env_var_name in env_vars:
                    env_variables.append(f"-e{env_var_name}={env_vars[env_var_name]}")

            if 'LDFLAGS' in os.environ:
                env_variables.append(f"-eLDFLAGS={os.environ['LDFLAGS']}")

            full_command = [
                get_runner(),
                "run",
                "-i",
                "--rm",
                f"-v{self._project_path}:/work",
            ]
            full_command += env_variables
            full_command += [
                container,
                command
            ]
            full_command += new_options

            logger.debug("Temp container command is: %s", shlex.join(full_command))

            result = subprocess.run(full_command)
        else:
            dir_set = "/work"

            common = os.path.commonprefix([self._project_path, os.getcwd()])
            if common != self._project_path:
                logger.error("Cannot run in non-subdirectory")
                return

            dir_set = dir_set + os.getcwd().replace(self._project_path, "")

            env_variables = []

            if 'LDFLAGS' in os.environ:
                env_variables.append(f"-eLDFLAGS={os.environ['LDFLAGS']}")

            full_command = [
                get_runner(),
                "exec",
                "-i",
                "--workdir", dir_set
            ]
            full_command += env_variables
            full_command += [
                running_name,
                command
            ]

            if new_options[0].strip() == command.strip():
                full_command += new_options[1:]
            else:
                full_command += new_options

            logger.debug("Container command is: %s", shlex.join(full_command))

            result = subprocess.run(full_command)

        if result.returncode != 0:
            sys.exit(result.returncode)