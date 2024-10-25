import os

from krillbuild.base import DevEnvBase

DOCKER_TEMPLATE_DIFFARCH=r"""FROM alpine:latest

RUN apk add -U wget gcc

RUN wget https://go.dev/dl/go1.23.1.linux-amd64.tar.gz -O go.tar.gz && \
tar -C /usr/local -zxf go.tar.gz && \
rm go.tar.gz

RUN mkdir -p /opt/toolchain && \
wget https://github.com/bocajspear1/static-toolchains/releases/download/latest/$TUPLE$-musl-toolchain.tar.gz  -O /tmp/toolchain.tar.gz && \
tar -zxvf /tmp/toolchain.tar.gz -C /opt/toolchain && \
rm /tmp/toolchain.tar.gz

RUN echo -e '#!/bin/sh\n/opt/toolchain/bin/$TUPLE$-gcc -L$LIBRARY_PATH "$@"\n' > /bin/crossgcc && \
    chmod +x /bin/crossgcc

RUN echo -e '#!/bin/sh\n/opt/toolchain/bin/$TUPLE$-g++ -L$LIBRARY_PATH "$@"\n' > /bin/crossg++ && \
    chmod +x /bin/crossg++

RUN rmdir /usr/local/bin && ln -s /usr/local/go/bin /usr/local/bin

RUN mkdir -p /work

WORKDIR /work
"""

DOCKER_TEMPLATE_NOARCH=r"""FROM alpine:latest

RUN apk add -U wget gcc g++

RUN wget https://go.dev/dl/go1.23.1.linux-amd64.tar.gz -O go.tar.gz && \
tar -C /usr/local -zxf go.tar.gz && \
rm go.tar.gz

RUN echo -e '#!/bin/sh\ngcc -L$LIBRARY_PATH "$@"\n' > /bin/crossgcc && \
    chmod +x /bin/crossgcc

RUN echo -e '#!/bin/sh\ng++ -L$LIBRARY_PATH "$@"\n' > /bin/crossg++ && \
    chmod +x /bin/crossg++

RUN rmdir /usr/local/bin && ln -s /usr/local/go/bin /usr/local/bin

RUN mkdir -p /work

WORKDIR /work
"""


class MuslGoDevEnvPlugin(DevEnvBase):

    ARCH_MAP = {
        "powerpc64": {
            "tuple": "powerpc64-linux-musl"
        },
        "arm": {
            "tuple": "arm-linux-musleabi"
        },
        "aarch64": {
            "tuple": "aarch64-linux-musl"
        },
        "mipsel": {
            "tuple": "mipsel-linux-musl"
        },
        "mips64": {
            "tuple": "mips64-linux-musl"
        },
    }

    TOOLS = {
        "gcc": "crossgcc",
        "g++": "crossg++",
        "go": "go",
        # "ar": "PREFIX-ar",
        "ld": "PREFIX-ld",
        "nm": "PREFIX-nm",
        "strip": "PREFIX-strip",
        "objcopy": "PREFIX-objcopy",
        "objdump": "PREFIX-objdump",
        "readelf": "PREFIX-readelf",
    }

    NOARCH_TUPLE = ('x86_64-win', 'x86-win', 'x86_64', 'x86')

    def get_image(self, arch):
        return f"krill-go-{arch}"
    
    def build(self, arch):
        container_name = self.get_image()

        arch_tuple = None
        docker_file_content = ""
        if arch in self.NOARCH_TUPLE:
            docker_file_content = DOCKER_TEMPLATE_NOARCH
        elif arch in self.ARCH_MAP:
            arch_tuple = self.ARCH_MAP[arch]['tuple']
            docker_file_content = DOCKER_TEMPLATE_DIFFARCH.replace("$TUPLE$", arch_tuple)
        else:
            raise ValueError("Unsupported arch")
        
        self.build_container(docker_file_content, container_name)

    def prepare_run(self, arch, tool, options):
        
        tool_command = ""

        all_tools = self.TOOLS
        
        if tool not in all_tools:
            tool_command = tool
        else:
            tool_template = all_tools[tool]
            if "PREFIX-" in tool_template:
                if arch in self.NOARCH_TUPLE:
                    tool_command = tool_template.replace("PREFIX-", "")
                else:
                    tool_command = "/opt/toolchain/bin/" + tool_template.replace("PREFIX-", self.ARCH_MAP[arch]['tuple'] + "-")
            else:
                tool_command = tool_template


        go_os = "linux"
        if "-win" in arch:
            go_os = "windows"
        
        go_arch = arch
        # I guess reverses it, guess its actually right but whatever
        if go_arch == "mipsel":
            go_arch = "mipsle"

        env_dict = {
            # "LD_LIBRARY_PATH": f"/work/.krill/{arch}/lib",
            "LIBRARY_PATH": f"/work/.krill/{arch}/lib",
            "C_INCLUDE_PATH": f"/work/.krill/{arch}/include",
            "CPLUS_INCLUDE_PATH": f"/work/.krill/{arch}/include",
            "INSTALL_DIR": f"/work/.krill/{arch}",
            "GOOS": go_os,
            "GOARCH": go_arch,
            "GOPATH": f"/work/.krill/{arch}/"
        }

        if tool == "go" and arch not in self.NOARCH_TUPLE:
            env_dict['CC'] = "/opt/toolchain/bin/" + self.ARCH_MAP[arch]['tuple'] + "-gcc"
            env_dict['CXX'] = "/opt/toolchain/bin/" + self.ARCH_MAP[arch]['tuple'] + "-g++"

        return tool_command, env_dict, options

    def get_tools(self, arch):
        ret_commands = []

        for command in self.TOOLS:
            ret_commands.append(command)
        
        return ret_commands
    
    def get_instant_env(self, arch):
        env_dict = {}
        extra_env = ('GOARM', 'GODEBUG', 'GOFLAGS', 'CGO_ENABLED', 'CGO_CFLAGS', 'CGO_CPPFLAGS', 'CGO_CXXFLAGS', 'CGO_LDFLAGS')
        for extra in extra_env:
            if extra in os.environ:
                env_dict[extra] = os.environ[extra]
        return env_dict