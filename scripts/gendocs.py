import click

from krillbuild import cli
from krillbuild.devenv_loader import KrillDevEnvs
from krillbuild.mod_loader import KrillMods

def recursive_help(cmd, parent=None, parent_str=None):

    output = ""

    ctx = click.core.Context(cmd, info_name=cmd.name, parent=parent)

    if parent_str is None:
        output += f"## {cmd.name}\n\n"
    else:
        output += f"## {parent_str} {cmd.name}\n\n"

    info_dict = ctx.to_info_dict()
    
    output += "```text\n" + cmd.get_help(ctx) + "\n```\n"
    # print(info_dict)
    commands = getattr(cmd, 'commands', {})
    for sub in commands.values():
        new_parent_str = ""
        if parent_str is None:
            new_parent_str = cmd.name
        else:
            new_parent_str = f"{parent_str} {cmd.name}"
        output += recursive_help(sub, ctx, new_parent_str)
    return output

def main():
    output = "# Commands\n\n"
    for subcommand in cli.commands.values():
        output += recursive_help(subcommand)
    
    with open("./docs/commands.md", "w") as outfile:
        outfile.write(output)

    # Generate docs for devenvs

    output = "# DevEnvs\n\n"
    devenvs = KrillDevEnvs()
    for devenv in devenvs.list_devenvs():
        if devenv.__module__.startswith("custom."):
            continue
        output += f"##{devenv.shortname}\n\n"
        output += f"{devenv.__doc__}\n\n"
        # print(devenv)

    with open("./docs/devenvs.md", "w") as outfile:
        outfile.write(output)

    # Generate docs for mods

    output = "# Mods\n\n"
    mods = KrillMods()
    for mod in mods.list_mods():
        # if devenv.__module__.startswith("custom."):
        #     continue
        output += f"##{mod.shortname}\n\n"
        output += f"{mod.__doc__}\n\n"
        # print(mod)

    with open("./docs/mods.md", "w") as outfile:
        outfile.write(output)




main()