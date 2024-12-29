

import re
import subprocess

def is_basic_string(in_str):
    if re.search(r"[^0-9a-zA-Z]", in_str) is not None:
        raise ValueError("String " + in_str + " contains more than alphanumeric characters")
    return in_str

def get_command_path(command):
    if re.search(r"[^-_0-9a-zA-Z]", command) is not None:
        raise ValueError("Attempting to find invalid command")
    which_command = subprocess.run("which " + command, shell=True, capture_output=True)
        
    if which_command.returncode == 0:
        return which_command.stdout.decode().strip()
    else:
        return None
    
def extract_file(file_path, destination):
    if ".tar" in file_path:
        command = [get_command_path("tar"), "-x", "-f", file_path, "-C", destination]
        print(command)
        subprocess.run(command)