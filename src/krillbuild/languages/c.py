from krillbuild.base import KrillPlugin

DOCKER_TEMPLATE=r"""FROM alpine:latest

RUN apk add -U wget clang lld

RUN mkdir -p /opt/toolchain && \
wget https://github.com/bocajspear1/static-toolchains/releases/download/latest/$TUPLE$-musl-toolchain.tar.gz  -O /tmp/toolchain.tar.gz && \
tar -zxvf /tmp/toolchain.tar.gz -C /opt/toolchain

RUN echo -e '#!/bin/sh\n/opt/toolchain/bin/$TUPLE$-gcc -L$LIBRARY_PATH "$@"\n' > /bin/crossgcc && \
    chmod +x /bin/crossgcc

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

class CPlugin(KrillPlugin):

    def build(self, arch):
        container_name = f"krill-c-{arch}"
        if arch == "powerpc":
            arch_tuple = "powerpc-linux-musl"
        elif arch == "arm":
            arch_tuple = "arm-linux-musleabi"
        else:
            raise ValueError("Unsupported arch")
        
        docker_file_content = DOCKER_TEMPLATE.replace("$TUPLE$", arch_tuple)

        self.build_container(docker_file_content, container_name)



    def prepare_compile(self, arch, options):
        container = ""
        if arch == "x86_64":
            container = "krill-c-x86_64"
        elif arch == "mipsel":
            container = f"krill-c-mipsel"
        elif arch == "powerpc":
            container = f"krill-c-powerpc"
        elif arch == "arm":
            container = f"krill-c-arm"

        command = "crossgcc"
        if options[0] == "--clang":
            command = "crossclang"
            options = options[1:]

        return container, command, {
            # "LD_LIBRARY_PATH": f"/work/.krill/{arch}/lib",
            "LIBRARY_PATH": f"/work/.krill/{arch}/lib",
            "C_INCLUDE_PATH": f"/work/.krill/{arch}/include",
            "CPLUS_INCLUDE_PATH": f"/work/.krill/{arch}/include",
            "INSTALL_DIR": f"/work/.krill/{arch}",
        }, options