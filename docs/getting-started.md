# Getting Started

## 0. KrillBuild Basics

KrillBuild utilizes containers to execute build chains and tools. This allows numerous build chains, even different versions of the same compiler, to exist simultaneously without messing with your system's build configurations. Containers are run via plugins, `devenv` plugins for compilers and their tools, and `mod` plugins for variation generation.

### DevEnv

Compiler toolsets are utilized via `devenv` (development environment) plugins. These will contain a compiler and supporting tools and libraries for different architectures.

### Mod

Tools like packers, encoders, and compressors are utilized via `mod` (modifier) plugins. These will contain the tool and its necessary libraries, but won't map commands like the DevEnv modules. This is to allow tracking of original and modified files for easy reversion or reference.

## 1. Installing KrillBuild

KrillBuild is a Python project. It is recommended to use it in a Python venv.

```
python3 -m venv ./venv
source ./venv/bin/activate
pip3 install krillbuild
```

You will also need to have Docker installed.

## 2. Create a Project

KrillBuild revolves around "projects". Projects contain the source code of your binary, but also work similar to Python `venv`s, containing dependencies as well.

!!! note

    Everything in a project will be mapped into the containers, so your build scripts can't reference anything directory on the host system or relatively outside the project's directory (e.g. `../../`). KrillBuild tries its best to replace absolute paths to the project in commands, but this shouldn't be relied on.

Create a project using the following command:

```
krillbuild project init
```

This creates the `.krill` directory, which will store dependencies (including cached downloads, build directories for each architecture, include directories, and library directories), cache of binary builds, and commands. This includes mapping tools inside containers to common commands on the host system to make re-using build scripts simple. (e.g. mapping a cross-compiling gcc to the command `gcc` on the host system.) KrillBuild does this by modifying environment variables very similar to Python venv. To activate KrillBuild's environment, run:

```shell
$ source ./.krill/bin/activate
Project path: /home/user/Code/project1
Current architecture: None
```

Note that it indicates no current architecture. KrillBuild allows you to switch between architectures and compilers to target for your binaries. This also makes some changes to environment variables, so needs to be activated similarly:

```shell
$ source activate_arch <DEVENV> <ARCHITECTURE>
Project path: /home/user/Code/project1
Current architecture: <ARCHITECTURE>
```

The current devenv and architecture will be shown in the front of the prompt similar to a venv.

```
<muslgo-arm> (venv) prompt$
```

## 3. Running DevEnv Tools

Before you can use devenvs you will need to build the containers for them them (You only need to do this once). To build a devenv for an architecture:

```shell
$ krillbuild devenv build <DEVENV_NAME> <ARCHITECTURE>
```

DevEnv plugins will set up a number of commands that will be mapped to commands inside the devenv's container. These command mappings will normally take care of things like setting up default library paths and include paths to simplify execution. (e.g. Set up the `gcc` compiler to look in the `.krill/<ARCHITECTURE>` directory for libraries and includes.) Available tools can be viewed with the `krillbuild devenv toollist`. The following is an example for the `muslgo` devenv.

```shell
$ krillbuild devenv toollist
# muslgo
    * gcc
    * g++
    * go
    * ld
    * nm
    * strip
    * objcopy
    * objdump
    * readelf
```

The following is a list for the `muslc` devenv:

```shell
$ krillbuild devenv toollist
# muslc
    * gcc
    * g++
    * clang
    * ld
    * nm
    * strip
    * objcopy
    * objdump
    * readelf
```

Once built and activated, each of the tools in the list are mapped to scripts in the `.krill/bin` that call the commands in the container, so with the KrillBuild project activated for the devenv `muslc` and the architecture `arm`, you can see call `gcc` now maps to the cross-compiler inside the container:

```shell
<muslc-arm> (venv) prompt$ gcc
arm-linux-musleabi-gcc: fatal error: no input files
compilation terminated.
```

This means with calling `gcc` we can create ARM archiecture binaries:

```shell
<muslc-arm> (venv) prompt$ gcc test.c -o project1.arm -static
<muslc-arm> (venv) prompt$ file project1.arm 
project1.arm: ELF 32-bit LSB executable, ARM, EABI5 version 1 (SYSV), statically linked, with debug_info, not stripped
```

Then we can switch architectures an easily make binaries in the MIPSEL architecture:

```shell
<muslc-arm> (venv) prompt$ source activate_arch muslc mipsel
Project path: /home/user/Code/project1
Current architecture: mipsel
<muslc-mipsel> (venv) prompt$ gcc test.c -o project1.mipsel -static
<muslc-mipsel> (venv) prompt$ file project1.mipsel
project1.mipsel: ELF 32-bit LSB executable, MIPS, MIPS-I version 1 (SYSV), statically linked, not stripped
```

## 4. Running Mod Plugins

Before you can use mod plugins you will need to build the containers for them them (You only need to do this once). To build a mod for an architecture:

```shell
$ krillbuild modbuild <DEVENV_NAME> <ARCHITECTURE>
```

Mod plugins can be run with the follow command structure:

```shell
krillbuild mod <MOD_PLUGIN>.<MOD_FUNCTION> -i <INPUT_FILENAME> -o <OUTPUT_FILENAME> -- <OPTIONS>
```

The functions in a mod plugin can be seen by just calling with a plugin name:

```shell
$ krillbuild mod encode
Provides encoding functionality.
    
    
 - base64
 - pwshbase64
 - cfile
```


Example for the `base64` function in the `encode` plugin:

```shell
$ krillbuild mod encode.base64 -i test.mipsel -o test.mipsel.base64
$ cat test.mipsel.base64
f0VMRgEBAQAAAAAAAAAAAAIACAABAAAAoAFAADQAAADIOQAABxAAADQAIAAFACgAFgAVAAMAAHDYAAAA2ABAANgAQAAYAAAAGAA...
```

## 5. Using INI files

KrillBuild's INI files allow for one set of commands to set build the same binary for multiple architectures as well as create variations of that binary. With one file, you can build a tool for many architectures, build its dependencies for multiple architectures, and create packed and unpacked versions for the built binary. Currently, KrillBuild utilizes the built-in INI file format for its build file. The default name for the INI file is `krill.ini`.

To make it easier to understand its abilities, let's step through an example INI file:

```ini
[krill]
devenv = muslc
archlist = mipsel,arm,aarch64,x86_64,x86_64-win

[lib.mbedtls]
source = https://github.com/Mbed-TLS/mbedtls/releases/download/mbedtls-3.6.1/mbedtls-3.6.1.tar.bz2
compiler = gcc
commands = 
    %%x86_64-win export WINDOWS_BUILD=1
    cd mbedtls*
    make -j2 lib
    make install DESTDIR=$KRILL_INSTALL_DIR 

[lib.curl]
source = https://curl.se/download/curl-8.10.1.tar.gz
compiler = gcc
commands =
    export LDFLAGS="-L$LIBRARY_PATH"
    %%x86_64-win export LIBS="-lbcrypt"
    env
    cd curl*
    ./configure --with-mbedtls --target=${KRILL_ARCH}-linux-musl --host=${KRILL_ARCH}-linux-musl --without-libpsl --enable-static --disable-shared --disable-ldap --disable-ldaps --prefix=$KRILL_INSTALL_DIR
    make -j2
    make install
    echo ""
    
[main]
compiler = gcc
commands =
    %%x86_64-win export EXTRA="-lbcrypt -lws2_32"
    gcc test.c -lcurl -lmbedtls -lmbedcrypto -lmbedx509 $EXTRA -o test.$KRILL_ARCH -static   


[mod.upx.upx]
infile = test.$KRILL_ARCH
outfile = test.$KRILL_ARCH
options = 
```

### Sections

#### `[krill]`

This section defines the devenv for the INI file and a list of desired architectures (comma separated).

#### `[lib.???]`

`lib` sections define dependencies to be built before any other code. Here you can define a source archive (which is cached) and the command commands needed to statically compile the library. KrillBuild will check to see if the library is already built or not and only build if the library is not found. It utilizes the name in the section's title after the dot.

!!! warning

    KrillBuild expects the resulting library to be static!

Since KrillBuild is using the built in INI format in Python, each command must be indented to indicate its still in the list of commands. In the example, some commands begin with `%%x86_64-win`, this indicates that this command only runs for the architecture name after the `%%`. In the example, this means it only runs for the `x86_64-win` architecture.

Commands in the command list are inputted to a shell, so can take advantage of shell environment variables. By default, KrillBuild will stop if the output of a command is not successful (return code other than `0`).

#### `[main]`

This section defines the commands for primary binary. Commands here should already be set up with proper include and library paths, allowing for less cluttered commands. In the example, it tells gcc to link the curl and mbedtls libraries without having to set the paths to the locations of those libraries. (For reference, they are located in `.krill/<ARCHITECTURE>`, which gcc is configured to look it). The line starting with `%%x86_64-win` creates an extra environment variable for when cross compiling to Windows that sets some options not needed on Linux builds.

Commands in the command list are inputted to a shell, so can take advantage of shell environment variables. By default, KrillBuild will stop if the output of a command is not successful (return code other than `0`).

#### `[mod.<MOD_PLUGIN>.<MOD_FUNCTION>]`

This section defines mods to run after the main section. These sections are intended to modify the built binary in any number of ways while tracking a history of the file for future reference. The input and output files must be set here to allow the file tracking. The names can utilize a few variables that KrillBuild will insert, such as `KRILL_ARCH`. The mod plugins' name and function are set in the section title, with the options set in the `option` key.

### Running a Build

To run a build, use the `krillbuild project build`. This will loop through each defined architecture and build dependencies, build the target binary, and then run mod plugins on each produced binary.

### Using Alternate INI Files

Alternate INI files can be set with `-p <FILE>` argument.

### Custom Plugins

KrillBuild INI files can configure a path to custom plugin Python (`.py`) file by setting the `path` value in the `[krill]` section. 