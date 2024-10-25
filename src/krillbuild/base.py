import subprocess
import shlex
import logging
import os
import tempfile
import stat

from krillbuild.runner import get_runner

logger = logging.getLogger('krillbuild')

class KrillPlugin():

    @property
    def name(self):
        return self.__class__.__name__

    def build_container(self, dockerfile_content, image_name):
        runner = get_runner()

        with tempfile.TemporaryDirectory() as tmpdirname:
            old_cwd = os.getcwd()

            os.chdir(tmpdirname)

            
            dockerfile_path = os.path.join(tmpdirname, f"Dockerfile.{image_name}")

            print(dockerfile_content)

            with open(dockerfile_path, "w") as dockerfile:
                dockerfile.write(dockerfile_content)
                dockerfile.flush()

            full_command = [
                runner,
                "build",
                "-f", dockerfile_path,
                "-t", image_name,
                tmpdirname
            ]

            logger.debug("Running build command %s", shlex.join(full_command))

            subprocess.run(full_command)

            os.chdir(old_cwd)

class DevEnvBase(KrillPlugin):

    def setup(self, project_path, arch):
        bin_dir = os.path.join(project_path, ".krill", "bin")

        old_tools = os.listdir(bin_dir)
        for item in old_tools:
            if item in ('activate', 'activate_arch'):
                continue
            old_path = os.path.join(bin_dir, item)
            os.unlink(old_path)

        for tool in self.get_tools(arch):
            tool_path = os.path.join(bin_dir, tool)
            with open(tool_path, "w") as tool_file:
                tool_file.write("#!/bin/sh\n")
                tool_file.write(f"krillbuild exec {tool} \"$@\"\n")
            os.chmod(tool_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IXOTH | stat.S_IROTH)

            prefix_tool_path = os.path.join(bin_dir, f"krill-{arch}-{tool}")
            with open(prefix_tool_path, "w") as tool_file:
                tool_file.write("#!/bin/sh\n")
                tool_file.write(f"krillbuild exec {tool} \"$@\"\n")
            os.chmod(prefix_tool_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IXOTH | stat.S_IROTH)

    def get_instant_env(self, arch):
        return None