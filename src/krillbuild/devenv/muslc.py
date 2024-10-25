from krillbuild.base import DevEnvBase

DOCKER_TEMPLATE=r"""FROM alpine:latest

RUN apk add -U wget clang lld

RUN mkdir -p /opt/toolchain && \
wget https://github.com/bocajspear1/static-toolchains/releases/download/latest/$TUPLE$-musl-toolchain.tar.gz  -O /tmp/toolchain.tar.gz && \
tar -zxvf /tmp/toolchain.tar.gz -C /opt/toolchain

RUN echo -e '#!/bin/sh\n/opt/toolchain/bin/$TUPLE$-gcc -L$LIBRARY_PATH "$@"\n' > /bin/crossgcc && \
    chmod +x /bin/crossgcc

RUN echo -e '#!/bin/sh\n/opt/toolchain/bin/$TUPLE$-g++ -L$LIBRARY_PATH "$@"\n' > /bin/crossg++ && \
    chmod +x /bin/crossg++

# Stuff for clang to cooperate
RUN mkdir -p /opt/toolchain/usr && \
    ln -s /opt/toolchain/$TUPLE$/include/ /opt/toolchain/usr/include && \
    ln -s /opt/toolchain/$TUPLE$/lib/ /opt/toolchain/usr/lib

# https://stackoverflow.com/questions/73776689/cross-compiling-with-clang-crtbegins-o-no-such-file-or-directory
RUN ln -s /opt/toolchain/lib/gcc/$TUPLE$/10.3.0/crtbeginT.o /opt/toolchain/usr/lib/crtbeginT.o && \
    ln -s /opt/toolchain/lib/gcc/$TUPLE$/10.3.0/crtend.o /opt/toolchain/usr/lib/crtend.o && \
    ln -s /opt/toolchain/lib/gcc/$TUPLE$/10.3.0/crtbeginT.o /opt/toolchain/usr/lib/crtbeginS.o && \
    ln -s /opt/toolchain/lib/gcc/$TUPLE$/10.3.0/crtend.o /opt/toolchain/usr/lib/crtendS.o && \
    ln -s /opt/toolchain/lib/gcc/$TUPLE$/10.3.0/crtbeginT.o /opt/toolchain/usr/lib/crtbegin.o

RUN echo -e '#!/bin/sh\nclang --target=$TUPLE$ --sysroot=/opt/toolchain/ -fuse-ld=lld -L/opt/toolchain/lib/gcc/$TUPLE$/10.3.0/ -L$LIBRARY_PATH "$@"\n' > /bin/crossclang && \
    chmod +x /bin/crossclang

RUN mkdir -p /work

WORKDIR /work
"""

MINGW32_DOCKER_TEMPLATE=r"""FROM alpine:latest

RUN apk add -U wget i686-mingw-w64-gcc gcc g++


RUN echo -e '#!/bin/sh\ni686-w64-mingw32-gcc -L$LIBRARY_PATH "$@"\n' > /bin/crossgcc && \
    chmod +x /bin/crossgcc

RUN echo -e '#!/bin/sh\ni686-w64-mingw32-g++ -L$LIBRARY_PATH "$@"\n' > /bin/crossg++ && \
    chmod +x /bin/crossg++

RUN mkdir -p /work

WORKDIR /work
"""

MINGW64_DOCKER_TEMPLATE=r"""FROM alpine:latest

RUN apk add -U wget mingw-w64-gcc gcc g++


RUN echo -e '#!/bin/sh\nx86_64-w64-mingw32-gcc -L$LIBRARY_PATH "$@"\n' > /bin/crossgcc && \
    chmod +x /bin/crossgcc

RUN echo -e '#!/bin/sh\nx86_64-w64-mingw32-g++ -L$LIBRARY_PATH "$@"\n' > /bin/crossg++ && \
    chmod +x /bin/crossg++

RUN mkdir -p /work

WORKDIR /work
"""

MY_ARCH_DOCKERFILE=r"""FROM alpine:latest

RUN apk add -U wget clang lld musl-dev gcc g++

RUN echo -e '#!/bin/sh\ngcc -L$LIBRARY_PATH "$@"\n' > /bin/crossgcc && \
    chmod +x /bin/crossgcc

RUN echo -e '#!/bin/sh\ng++ -L$LIBRARY_PATH "$@"\n' > /bin/crossg++ && \
    chmod +x /bin/crossg++

RUN echo -e '#!/bin/sh\nclang -fuse-ld=lld -L$LIBRARY_PATH "$@"\n' > /bin/crossclang && \
    chmod +x /bin/crossclang

RUN mkdir -p /work

WORKDIR /work
"""

class MuslCDevEnvPlugin(DevEnvBase):

    ARCH_MAP = {
        "powerpc": {
            "tuple": "powerpc-linux-musl"
        },
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
        "clang": "crossgclang",
        # "ar": "PREFIX-ar",
        "ld": "PREFIX-ld",
        "nm": "PREFIX-nm",
        "strip": "PREFIX-strip",
        "objcopy": "PREFIX-objcopy",
        "objdump": "PREFIX-objdump",
        "readelf": "PREFIX-readelf",
    }

    WIN_EXTRA_TOOLS = {
        'windres': "PREFIX-windres", 
        'dlltool': "PREFIX-dlltool"
    }

    def get_image(self, arch):
        return f"krill-c-{arch}"

    def build(self, arch):
        container_name = self.get_image(arch)

        arch_tuple = None
        docker_file_content = ""
        if arch == "x86_64":
            docker_file_content = MY_ARCH_DOCKERFILE
        elif arch == "x86-win":
            docker_file_content = MINGW32_DOCKER_TEMPLATE
        elif arch == "x86_64-win":
            docker_file_content = MINGW64_DOCKER_TEMPLATE
        elif arch in self.ARCH_MAP:
            arch_tuple = self.ARCH_MAP[arch]['tuple']
            docker_file_content = DOCKER_TEMPLATE.replace("$TUPLE$", arch_tuple)
        else:
            raise ValueError("Unsupported arch")
        
        self.build_container(docker_file_content, container_name)

    def prepare_run(self, arch, tool, options):
     
        tool_command = ""

        all_tools = self.TOOLS
        all_tools.update(self.WIN_EXTRA_TOOLS)
        
        if tool not in all_tools:
            tool_command = tool
        else:
            tool_template = all_tools[tool]
            if "PREFIX-" in tool_template:
                prefix = ""
                if arch == "x86-win":
                    prefix = "i686-w64-mingw32"
                elif arch == "x86_64-win":
                    prefix = "x86_64-w64-mingw32"
                elif arch == "x86_64":
                    prefix = ""
                elif arch in self.ARCH_MAP:
                    prefix = "/opt/toolchain/bin/" + self.ARCH_MAP[arch]['tuple']
                
                tool_command = ""
                if prefix != "":
                    tool_command = f"{prefix}-{tool}"
                else:
                    tool_command = tool
            else:
                tool_command = tool_template


        return tool_command, {
            # "LD_LIBRARY_PATH": f"/work/.krill/{arch}/lib",
            "LIBRARY_PATH": f"/work/.krill/{arch}/lib",
            "C_INCLUDE_PATH": f"/work/.krill/{arch}/include",
            "CPLUS_INCLUDE_PATH": f"/work/.krill/{arch}/include",
            "INSTALL_DIR": f"/work/.krill/{arch}",
        }, options

    def get_tools(self, arch):
        ret_commands = []
        
        if "-win" in arch:
            for command in self.WIN_EXTRA_TOOLS:
                ret_commands.append(command)
        for command in self.TOOLS:
            ret_commands.append(command)
        
        return ret_commands