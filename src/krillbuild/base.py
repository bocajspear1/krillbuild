import subprocess
import shlex
import logging
import os
import tempfile

from krillbuild.runner import get_runner

logger = logging.getLogger('krillbuild')

class KrillPlugin():

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