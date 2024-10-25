import click
import logging
import os

import coloredlogs

logger = logging.getLogger('krillbuild')

from krillbuild.compile import KrillBuild
from krillbuild.project import KrillProject
from krillbuild.devenv_loader import KrillDevEnvs
from krillbuild.mod_loader import KrillMods


@click.group()
@click.option('--debug', is_flag=True, default=False)
def cli(debug):
    if os.getenv("KRILL_PROJECT"):
        log_path = os.path.join(os.getenv("KRILL_PROJECT"), "krillbuild.log")
    else:
        log_path = "krillbuild.log"
    handlers = [
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
    if debug:
        logging.basicConfig(level=logging.DEBUG, handlers=handlers)
        coloredlogs.install(level='DEBUG')
    else:
        logging.basicConfig(level=logging.INFO, handlers=handlers)
        coloredlogs.install(level='INFO')

        

@click.command()
@click.argument('mod')
@click.argument('arch')
def modbuild(mod, arch):
    mod_loader = KrillMods()
    mod = mod_loader.get_mod(mod)
    mod.build(arch)

@click.command(context_settings={"ignore_unknown_options": True})
@click.option('devenv', '--devenv', envvar='KRILL_DEV_ENV')
@click.option('arch', '--arch', envvar='KRILL_ARCH')
@click.argument('tool')
@click.argument('options', nargs=-1)
def exec(devenv, arch, tool, options):
    
    loader = KrillDevEnvs()
    devenv_obj = loader.get_devenv(devenv)
    project_obj = KrillProject.get_project()
    if project_obj is not None:
        project_obj.run_devenv_tool(devenv_obj, tool, arch, options)
    else:
        print("Must activate a project first")

    


@click.group('devenv')
def devenv_group():
    pass

@devenv_group.command("build")
@click.argument('name')
@click.argument('arch')
def devenv_build(name, arch):
    loader = KrillDevEnvs()
    devenv_obj = loader.get_devenv(name)
    if devenv_obj is None:
        print("Invalid devenv")
        return 1
    devenv_obj.build(arch)

@devenv_group.command("setup")
@click.option('devenv', '--devenv', envvar='KRILL_DEV_ENV')
@click.option('arch', '--arch', envvar='KRILL_ARCH')
def devenv_setup(devenv, arch):
    if devenv is None:
        print("DevEnv not set")
        return 1
    if arch is None:
        print("Arch not set")
        return 1
    loader = KrillDevEnvs()
    devenv_obj = loader.get_devenv(devenv)
    project_obj = KrillProject.get_project()
    if project_obj is not None:
        devenv_obj.setup(project_obj.path, arch)
    else:
        print("Must activate a project first")
    

@devenv_group.command("list")
def devenv_list():
   loader = KrillDevEnvs()
   for item in loader.list_devenvs():
       print(f" - {item.shortname}")

@devenv_group.command("toollist")
@click.option('devenv', '--devenv', envvar='KRILL_DEV_ENV')
@click.option('arch', '--arch', envvar='KRILL_ARCH')
def devenv_toollist(devenv, arch):
    if devenv is None:
        print("DevEnv not set")
        return 1
    if arch is None:
        print("Arch not set")
        return 1
    loader = KrillDevEnvs()
    for devenv_obj in loader.list_devenvs():
        print(f"# {devenv_obj.shortname}")
        tool_list = devenv_obj.get_tools(arch)
        for tool in tool_list:
            print(f"    * {tool}")


@click.group()
def project():
    pass

@project.command("init")
@click.argument('project_dir', required=False)
def project_init(project_dir):
    if project_dir is None:
        project_dir = os.getcwd()
    print(project_dir)
    project = KrillProject.init(project_dir)

@project.command("build")
@click.option('inipath', '-p', default=None)
def project_build(inipath):
    project_obj = KrillProject.get_project()
    if project_obj is not None:
        if inipath is None:
            initpath = os.path.join(project_obj.path, "krill.ini")
        project_obj.run_build(initpath)
    else:
        print("Must activate a project first")

@project.command("stop")
@click.option('devenv', '--devenv', envvar='KRILL_DEV_ENV')
@click.option('arch', '--arch', envvar='KRILL_ARCH')
def project_stop(devenv, arch):
    loader = KrillDevEnvs()
    project_obj = KrillProject.get_project()
    if project_obj is not None:
        devenv_obj = loader.get_devenv(devenv)
        if devenv_obj is None:
            print("Invalid devenv")
            return 1
        project_obj.stop_devenv(devenv_obj, arch)
    else:
        print("Must activate a project first")

@project.command("info")
def project_info():
    project_obj = KrillProject.get_project()
    if project_obj is not None:
        project_obj.info()

@project.command("mod", context_settings={"ignore_unknown_options": True})
@click.argument('modname')
@click.argument('filename')
@click.argument('options', nargs=-1)
def project_compile(modname, filename, options):
    krill_proj = KrillProject.get_project()
    if krill_proj is not None:
        krill_proj.run_mod_command(modname, filename, options)

cli.add_command(modbuild)
cli.add_command(project)
cli.add_command(devenv_group)
cli.add_command(exec)

def main():
     cli()

if __name__ == '__main__':
   main()
