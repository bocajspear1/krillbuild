import os
import subprocess
import hashlib
import logging
import time
import shlex
import stat
import sys
import signal
import shutil

from termcolor import cprint

logger = logging.getLogger('krillbuild')

from krillbuild.util import extract_file

activate_script_sh="""
export PATH={project_path}/.krill/bin/:$PATH
export KRILL_PROJECT={project_path}
export KRILL_OLD_PS=$PS1
export PS1="\\[krill\\] $PS1"
krillbuild project info
"""

activate_arch_script_sh="""

if [ -z "$KRILL_PROJECT" ]; then
    echo "Activate project first"
else

KRILL_DEV_ENV='invalid'
if [ -z "$1" ]; then
    echo "Dev environment must be set"
else
    KRILL_DEV_ENV=$1
fi

KRILL_ARCH='invalid'
if [ -z "$2" ]; then
    echo "Architecture must be set"
elif [ "$2" == "any" ]; then
    KRILL_ARCH=$2
{arch_cond}
else
    echo "Invalid architecture"
fi

if [ "$KRILL_ARCH" != "invalid" ]; then
    export KRILL_INSTALL_DIR={project_path}/.krill/${{KRILL_ARCH}}
    export KRILL_ARCH
    export KRILL_DEV_ENV
    mkdir -p {project_path}/.krill/${{KRILL_ARCH}}/lib
    mkdir -p {project_path}/.krill/${{KRILL_ARCH}}/bin
    mkdir -p {project_path}/.krill/${{KRILL_ARCH}}/include
    export PS1="<${{KRILL_DEV_ENV}}-${{KRILL_ARCH}}> $KRILL_OLD_PS"
    krillbuild project info
    krillbuild devenv setup
fi

fi 

"""

from krillbuild.runner import get_runner
from krillbuild.devenv_loader import KrillDevEnvs
from krillbuild.mod_loader import KrillMods
from krillbuild.architectures import ARCHITECTURE_LIST
from krillbuild.compile import KrillBuild

class KrillProject():

    @classmethod
    def init(cls, project_path, dir_path=".krill"):
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
            os.mkdir(os.path.join(dir_path, "bin"))
            os.mkdir(os.path.join(dir_path, "build"))
            # os.mkdir(os.path.join(path, "bin"))
        
        activate_path = os.path.join(dir_path, "bin", "activate")
        with open(activate_path, "w") as activate_file:
            activate_file.write(activate_script_sh.format(project_path=project_path))

        activate_arch_path = os.path.join(dir_path, "bin", "activate_arch")
        with open(activate_arch_path, "w") as activate_file:

            arch_cond = ""
            for arch in ARCHITECTURE_LIST:
                arch_cond += f"elif [ \"$2\" == \"{arch}\" ]; then\n"
                arch_cond += f"    KRILL_ARCH=$2\n"

            activate_file.write(activate_arch_script_sh.format(project_path=project_path, arch_cond=arch_cond))
        os.chmod(activate_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IXOTH | stat.S_IROTH)
        
    @classmethod
    def get_project(cls):

        if 'KRILL_PROJECT' in os.environ:
            project_obj = cls(os.environ['KRILL_PROJECT'], os.getenv('KRILL_ARCH'))
            return project_obj
        else:
            return None
        
    def __init__(self, project_path, arch, temp=False):
        self._devenv_loader = KrillDevEnvs()
        self._mod_loader = KrillMods()
        self._project_path = os.path.abspath(project_path)
        self._arch = arch
        self._temp = temp

    @property
    def path(self):
        return self._project_path
    
    @property
    def arch(self):
        return self._arch
    
    @property
    def temp(self):
        return self._temp
    
    def get_mod(self, modname):
        return self._mod_loader.get_mod(modname)
    
    def get_running_name(self, plugin_cont_name):
        project_path_hash = hashlib.md5(self._project_path.encode()).hexdigest()
        return f"krill{project_path_hash}-{plugin_cont_name}"
    
    def info(self):
        current_arch = self._arch
        project_path = self._project_path

        print(f"Project path: {project_path}")
        print(f"Current architecture: {current_arch}")

    def _container_running(self, running_name):
        inspect_command = [
            get_runner(),
            "inspect",
            running_name
        ]

        logger.debug("Inspecting for project container '%s' with %s", running_name, shlex.join(inspect_command))

        result = subprocess.run(inspect_command, capture_output=True)
        if result.returncode != 0:
            return False
        else:
            return True
        
    def _start_container(self, container_name, running_name, env_vars):
        env_var_list = []

        if env_vars is not None:
            for env_var_name in env_vars:
                env_var_list.append(f"-e{env_var_name}={env_vars[env_var_name]}")
        
        full_command = [
            get_runner(),
            "run", "-d", 
            "--rm",
            f"--name={running_name}", 
            f"-v{self._project_path}:/work"
        ]
        full_command += env_var_list
        full_command += [
            container_name,
            "sh", "-c", "while [ 1 ]; do sleep 5; done"
        ]
        logger.info("Starting plugin container '%s' with %s", container_name, shlex.join(full_command))
        new_proc = subprocess.Popen(full_command)
        time.sleep(6)
        if new_proc.wait(30) != 0:
            logger.error("Container failed to start!")
            logger.error("Output: %s", new_proc.stderr.read().decode())
            return
        else:
            logger.info("Started plugin container")

    def stop_devenv(self, devenv_plugin, arch):
        container = devenv_plugin.get_image(arch)
        running_name = self.get_running_name(container)
        if not self._container_running(running_name):
            logger.error("Devenv %s is not running", devenv_plugin.shortname)
            return 1
        full_command = [
            get_runner(),
            "stop",
            running_name
        ]
        logger.info("Stopping project container with %s", shlex.join(full_command))
        new_proc = subprocess.run(full_command)
        return new_proc.returncode


    def run_devenv_tool(self, devenv_plugin, tool, arch, options):
        container = devenv_plugin.get_image(arch) 
        command, env_vars, new_options = devenv_plugin.prepare_run(arch, tool, options)

        running_name = self.get_running_name(container)
        if not self._container_running(running_name):
            self._start_container(container, running_name, env_vars)

        if new_options is None:
            new_options = []
        else:
            new_options = list(new_options)

        # Replace any options containing project path to container path
        for i in range(len(new_options)):
            if self._project_path in new_options[i]:
                new_options[i] = new_options[i].replace(self._project_path, "/work")


        dir_set = "/work"

        common = os.path.commonprefix([self._project_path, os.getcwd()])
        if common != self._project_path:
            logger.error("Cannot run in non-subdirectory")
            return

        dir_set = dir_set + os.getcwd().replace(self._project_path, "")

        env_variables = []

        if 'LDFLAGS' in os.environ:
            env_variables.append(f"-eLDFLAGS={os.environ['LDFLAGS']}")

        instant_env = devenv_plugin.get_instant_env(arch)
        if instant_env is not None:
            for instant_env_var_name in instant_env:
                env_variables.append(f"-e{instant_env_var_name}={instant_env[instant_env_var_name]}")

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

        if len(new_options) > 0 and new_options[0].strip() == command.strip():
            full_command += new_options[1:]
        else:
            full_command += new_options

        logger.debug("Container command is: %s", shlex.join(full_command))

        result = subprocess.run(full_command)

        if result.returncode != 0:
            sys.exit(result.returncode)

    def create_arch_dir(self, arch):
        arch_dir = os.path.join(self.path, ".krill", arch)
        if not os.path.exists(arch_dir):
            os.mkdir(arch_dir)
        
        dir_list = [
            os.path.join(arch_dir, "bin"),
            os.path.join(arch_dir, "lib"),
            os.path.join(arch_dir, "include")
        ]
        for dir_item in dir_list:
            if not os.path.exists(dir_item):
                os.mkdir(dir_item)

        return arch_dir
        

    def run_command_list(self, arch, command_list, env_vars, prefix, container_name=None, shell="/bin/sh", args="-i", do_chmod=True):
        command_sep = "KRILLSEP--KRILLSEP"
        result_command = "echo $? >&2"
        env_vars["PS1"] = "\n" + command_sep + "\n"

        old_commands = command_list
        command_list = []
        for item in old_commands:
            if item.startswith("%%"):
                start_split = item.split(" ", maxsplit=1)
                print(arch, start_split[0][2:])
                if arch != start_split[0][2:]:
                    continue
                else:
                    command_list.append(start_split[1])
                    command_list.append(result_command)
            else:
                command_list.append(item)
                command_list.append(result_command)

        command_list.append("exit")
        if do_chmod:
            command_list = ["chmod -R 777 ./"] + command_list

        def handler(signum, frame):
            print("got signal")
            sub_shell.stdin.close()
            sub_shell.kill()

        def preexec_function():
            signal.signal(signal.SIGINT, handler)

        sub_shell = subprocess.Popen([shell] + shlex.split(args), stdin=subprocess.PIPE, stderr=subprocess.PIPE, env=env_vars, preexec_fn=preexec_function)

        find_result = False
        last_result = 0
        for command in command_list:
            command = command.strip().encode()

            done = False
            buffer = b""

            while not done:
                char = sub_shell.stderr.read(1)
                if char == b"\n":
                    if command_sep.encode() in buffer:
                        buffer = buffer.replace(command_sep.encode(), b"")
                        sys.stderr.buffer.write(buffer + b"\n")
                        sys.stderr.buffer.flush()
                        buffer = b""

                        if command == b"exit":
                            sub_shell.communicate(command)
                        else:
                            if command == result_command.encode():
                                find_result = True
                            else:
                                cprint(f"<{prefix}> ==> {command.decode()}", "green")
                            sub_shell.stdin.write(command + b"\n")
                            sub_shell.stdin.flush()

                        done = True
                    else:
                        
                        if not find_result:
                            sys.stderr.buffer.write(buffer + b"\n")
                            sys.stderr.buffer.flush()
                            buffer = b""
                        else:
                            if buffer.decode() != "":
                                last_result = int(buffer.decode().strip())
                                if last_result != 0:
                                    logger.error("Build failed")
                                    sys.exit(last_result)
                                find_result = False
                                buffer = b""
                else:
                    buffer += char

    def run_build(self, krill_path):
        build = KrillBuild(krill_path)
        ok = build.load()
        if not ok:
            logger.error("Failed to load config file %s", krill_path)
            return
        
        devenv_obj = self._devenv_loader.get_devenv(build.devenv)
        if devenv_obj is None:
            logger.error("Invalid devenv '%s'", build.devenv)
            return

        for arch in build.architectures:
            bin_path = os.path.join(self.path, ".krill", "bin")
            arch_lib_path = os.path.join(self.path, ".krill", arch, "lib")
            cache_dir = os.path.join(self.path, ".krill", "cache")
            build_base_dir = os.path.join(self.path, ".krill", "build")
            if not os.path.exists(cache_dir):
                os.mkdir(cache_dir)

            arch_dir = self.create_arch_dir(arch)
            sub_env_add = {
                "KRILL_ARCH": arch,
                "KRILL_INSTALL_DIR": arch_dir,
                "KRILL_DEV_ENV": build.devenv,
                "LIBRARY_PATH": arch_lib_path
            }

            sub_env = os.environ.copy()
            sub_env.update(sub_env_add)

            sub_env['PATH'] = bin_path + ":" + sub_env['PATH']

            devenv_obj.setup(self.path, arch)

            for library in build.libraries:
                
                
                if not library.exists(arch_lib_path):

                    logger.info("Library %s:%s not found, building...", arch, library.name)

                    download_path = library.download(cache_dir)
                    build_dir = os.path.join(build_base_dir, f"{arch}-{library.name}")
                    if os.path.exists(build_dir):
                        shutil.rmtree(build_dir)
                    os.mkdir(build_dir)
                    os.chmod(build_dir, 0o0777)
                    extract_file(download_path, build_dir)

                    os.chdir(build_dir)

                    commands = library.commands.split("\n")

                    # commands = ['env', 'ls -la']
                    sub_env['CC'] = f"krillbuild --debug exec {library.compiler}"
                    self.run_command_list(arch, commands, sub_env, arch)
            

            os.chdir(self.path)
            main_object = build.main
            commands = main_object.commands.split("\n")

            print(commands)

            sub_env['CC'] = f"krillbuild exec {main_object.compiler}"
            self.run_command_list(arch, commands, sub_env, arch, do_chmod=False)
                    
                                




    # def init_container(self, language, options):

    #     if self.temp:
    #         return
        
    #     lang_plugin = self.get_language(language)

    #     container, command, env_vars, new_options = lang_plugin.prepare_compile(self._arch, options)

        

    #     print(container)

    #     running_name = self.get_running_name(lang_plugin.shortname, self._arch)

    #     runner = get_runner()

    #     inspect_command = [
    #         runner,
    #         "inspect",
    #         running_name
    #     ]

    #     logger.info("Inspecting for project container '%s' with %s", container, shlex.join(inspect_command))


    #     result = subprocess.run(inspect_command, capture_output=True)
    #     if result.returncode != 0:
            

    # def stop_container(self, language, options):
    #     lang_plugin = self.get_language(language)
    #     running_name = self.get_running_name(lang_plugin.shortname,  self._arch)

    #     runner = get_runner()

    #     inspect_command = [
    #         runner,
    #         "inspect",
    #         running_name
    #     ]

    #     logger.info("Inspecting for project container with %s", shlex.join(inspect_command))


    #     result = subprocess.run(inspect_command, capture_output=True)
    #     if result.returncode == 0:
    #         full_command = [
    #             runner,
    #             "stop",
    #             running_name
    #         ]
    #         logger.info("Stopping project container with %s", shlex.join(full_command))
    #         new_proc = subprocess.run(full_command)



    # def run_mod_command(self, mod, filename, options):
    #     mod_plugin = self.get_mod(mod)
    #     running_name = self.get_running_name(mod_plugin.shortname, self._arch)
    #     container, command, env_vars, new_options = mod_plugin.prepare_mod(self._arch, filename, list(options))

    #     env_variables = []

    #     if env_vars is not None:
    #         for env_var_name in env_vars:
    #             env_variables.append(f"-e{env_var_name}={env_vars[env_var_name]}")

    #     full_command = [
    #         get_runner(),
    #         "run",
    #         "-i",
    #         "--rm",
    #         f"-v{self._project_path}:/work",
    #     ]
    #     full_command += env_variables
    #     full_command += [
    #         container,
    #         command
    #     ]
    #     full_command += new_options

    #     logger.debug("Temp container command is: %s", shlex.join(full_command))

    #     result = subprocess.run(full_command)

    # def run_build_command(self, language, options):
    #     lang_plugin = self.get_language(language)
    #     running_name = self.get_running_name(lang_plugin.shortname, self._arch)
    #     container, command, env_vars, new_options = lang_plugin.prepare_compile(self._arch, options)
    #     result = None

        
    #     if self._temp:

    #         env_variables = []

            
    #         if env_vars is not None:
    #             for env_var_name in env_vars:
    #                 env_variables.append(f"-e{env_var_name}={env_vars[env_var_name]}")

    #         if 'LDFLAGS' in os.environ:
    #             env_variables.append(f"-eLDFLAGS={os.environ['LDFLAGS']}")

    #         full_command = [
    #             get_runner(),
    #             "run",
    #             "-i",
    #             "--rm",
    #             f"-v{self._project_path}:/work",
    #         ]
    #         full_command += env_variables
    #         full_command += [
    #             container,
    #             command
    #         ]
    #         full_command += new_options

    #         logger.debug("Temp container command is: %s", shlex.join(full_command))

    #         result = subprocess.run(full_command)
    #     else:
            

        