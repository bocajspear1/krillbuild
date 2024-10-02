import logging
import subprocess

logger = logging.getLogger('krillbuild')

RUNNER = ""

def get_runner():
    global RUNNER

    if RUNNER == "" or RUNNER is None:
        which_podman = subprocess.run("which podman", shell=True, capture_output=True)
        which_docker = subprocess.run("which docker", shell=True, capture_output=True)
        
        if which_podman.returncode == 0:
            RUNNER = which_podman.stdout.decode().strip()
        elif which_docker.returncode == 0:
            RUNNER = which_docker.stdout.decode().strip()
        else:
            raise ValueError("Could not find podman or docker!")
        
        logger.debug("Loaded container runner: %s", RUNNER)
    
    return RUNNER

   