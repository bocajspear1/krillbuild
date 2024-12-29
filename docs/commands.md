# Commands

## modbuild

```text
Usage: modbuild [OPTIONS] MOD ARCH

  Run the container build for the module MOD and architecture ARCH

Options:
  --help  Show this message and exit.
```
## project

```text
Usage: project [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  build
  files    Commands for managing tracked project files
  info     Get current project info
  init
  stop
  stopmod
```
## project init

```text
Usage: project init [OPTIONS] [PROJECT_DIR]

Options:
  --help  Show this message and exit.
```
## project build

```text
Usage: project build [OPTIONS]

Options:
  -p TEXT  Alternate path to INI file
  --help   Show this message and exit.
```
## project stop

```text
Usage: project stop [OPTIONS]

Options:
  --devenv TEXT
  --arch TEXT
  --help         Show this message and exit.
```
## project stopmod

```text
Usage: project stopmod [OPTIONS] MODNAME

Options:
  --arch TEXT
  --help       Show this message and exit.
```
## project files

```text
Usage: project files [OPTIONS] COMMAND [ARGS]...

  Commands for managing tracked project files

Options:
  --help  Show this message and exit.

Commands:
  clear  Clear all tracked files from project
  list   List tracked files for project.
```
## project files list

```text
Usage: project files list [OPTIONS]

  List tracked files for project. List includes "parent" files, files from
  which the file was modified from.

Options:
  --help  Show this message and exit.
```
## project files clear

```text
Usage: project files clear [OPTIONS]

  Clear all tracked files from project

Options:
  --help  Show this message and exit.
```
## project info

```text
Usage: project info [OPTIONS]

  Get current project info

Options:
  --help  Show this message and exit.
```
## devenv

```text
Usage: devenv [OPTIONS] COMMAND [ARGS]...

  Commands for managing devenvs

Options:
  --help  Show this message and exit.

Commands:
  build     Run container build for devenv NAME with architecture ARCH
  list      List all devenvs, including custom ones
  setup
  toollist  List tools available for current devenv (if activated) or all...
```
## devenv build

```text
Usage: devenv build [OPTIONS] NAME ARCH

  Run container build for devenv NAME with architecture ARCH

Options:
  -p TEXT  Path to alternate INI file
  --help   Show this message and exit.
```
## devenv setup

```text
Usage: devenv setup [OPTIONS]

Options:
  --devenv TEXT
  --arch TEXT
  --help         Show this message and exit.
```
## devenv list

```text
Usage: devenv list [OPTIONS]

  List all devenvs, including custom ones

Options:
  --help  Show this message and exit.
```
## devenv toollist

```text
Usage: devenv toollist [OPTIONS]

  List tools available for current devenv (if activated) or all devenvs

Options:
  --devenv TEXT  Name of devenv to use, uses environment variable
                 KRILL_DEV_ENV if available.
  --arch TEXT    Devenv architecture to use, uses environment variable
                 KRILL_ARCH if available.
  --help         Show this message and exit.
```
## exec

```text
Usage: exec [OPTIONS] TOOL [OPTIONS]...

Options:
  --devenv TEXT
  --help         Show this message and exit.
```
## mod

```text
Usage: mod [OPTIONS] MODSELECT [OPTIONS]...

  Run a mod plugin against 'infile' and output to 'outfile'. 'modselect' is
  'mod_name.mod_function'.

Options:
  --arch TEXT         Architecture to use
  -i, --infile TEXT   Input file
  -o, --outfile TEXT  Output file
  --help              Show this message and exit.
```
