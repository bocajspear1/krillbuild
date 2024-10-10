import click
import logging
import os

logger = logging.getLogger('krillbuild')

from krillbuild.config import Config
from krillbuild.compile import KrillBuild
from krillbuild.project import KrillProject
from krillbuild.language_loader import KrillLanguages
from krillbuild.mod_loader import KrillMods
from krillbuild.compiler_loader import KrillCompilers

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
    else:
        logging.basicConfig(level=logging.INFO, handlers=handlers)

@click.command()
@click.argument('compiler')
@click.argument('arch')
def compilerbuild(compiler, arch):
    if arch is None:
        print("Must set an architecture first")
        return
    compiler_load = KrillCompilers()
    compiler_plugin = compiler_load.get_compiler(compiler)
    compiler_plugin.build(arch)

@click.command()
@click.argument('mod')
@click.argument('arch')
def modbuild(mod, arch):
    mod_loader = KrillMods()
    mod = mod_loader.get_mod(mod)
    mod.build(arch)

@click.command()
def prebuild():
    click.echo('Do the prebuilding')

@click.command()
def postbuild():
    click.echo('Do the postbuilding')


@click.command(context_settings={"ignore_unknown_options": True})
@click.argument('compiler')
@click.option('arch', '--arch', envvar='KRILL_ARCH')
@click.argument('options', nargs=-1)
def compiler(compiler, arch, options):
    if arch is None:
        print("Must set an architecture first")
        return
    compiler_load = KrillCompilers()
    compiler_plugin = compiler_load.get_compiler(compiler)

    krill_proj = KrillProject.get_project()

    if krill_proj is None:
        krill_proj = KrillProject(os.getcwd(), arch, temp=True)
    
    krill_proj.run_plugin(compiler_plugin, arch, options)

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
cli.add_command(compilerbuild)
cli.add_command(prebuild)
cli.add_command(postbuild)
cli.add_command(project)
cli.add_command(compiler)

def main():
     cli()

if __name__ == '__main__':
   main()
