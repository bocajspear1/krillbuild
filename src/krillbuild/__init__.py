import click
import logging
import os

logger = logging.getLogger('krillbuild')

from krillbuild.config import Config
from krillbuild.compile import KrillCompile
from krillbuild.project import KrillProject
from krillbuild.language_loader import KrillLanguages
from krillbuild.mod_loader import KrillMods

@click.group()
@click.option('--debug', is_flag=True, default=False)
def cli(debug):
    handlers = [
        logging.FileHandler("krillbuild.log"),
        logging.StreamHandler()
    ]
    if debug:
        logging.basicConfig(level=logging.DEBUG, handlers=handlers)
    else:
        logging.basicConfig(level=logging.INFO, handlers=handlers)

@click.command()
@click.argument('language')
@click.argument('arch')
def langbuild(language, arch):
    lang_loader = KrillLanguages()
    language = lang_loader.get_language(language)
    language.build(arch)

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
@click.argument('language')
@click.argument('arch')
@click.argument('options', nargs=-1)
def compile(language, arch, options):
    krill_proj = KrillProject.get_project()

    if krill_proj is None:
        krill_proj = KrillProject(os.getcwd(), arch, temp=True)

    compiler = KrillCompile()
    compiler.compile(krill_proj, language, options)

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

@project.command("start")
@click.argument('language')
def project_start(language):
    project_obj = KrillProject.get_project()
    if project_obj is not None:
        project_obj.init_container(language, [])

@project.command("stop")
@click.argument('language')
def project_start(language):
    project = KrillProject.get_project()
    project.stop_container(language, [])

@project.command("info")
def project_info():
    project_obj = KrillProject.get_project()
    if project_obj is not None:
        project_obj.info()

@project.command("compile", context_settings={"ignore_unknown_options": True})
@click.argument('language')
@click.argument('options', nargs=-1)
def project_compile(language, options):
    krill_proj = KrillProject.get_project()
    if krill_proj is not None:
        compiler = KrillCompile()
        compiler.compile(krill_proj, language, options)

@project.command("mod", context_settings={"ignore_unknown_options": True})
@click.argument('modname')
@click.argument('filename')
@click.argument('options', nargs=-1)
def project_compile(modname, filename, options):
    krill_proj = KrillProject.get_project()
    if krill_proj is not None:
        krill_proj.run_mod_command(modname, filename, options)

cli.add_command(modbuild)
cli.add_command(langbuild)
cli.add_command(prebuild)
cli.add_command(postbuild)
cli.add_command(compile)
cli.add_command(project)

def main():
     cli()

if __name__ == '__main__':
   main()
