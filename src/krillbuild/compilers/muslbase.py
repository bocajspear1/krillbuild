from krillbuild.base import KrillPlugin

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

class MuslBase(KrillPlugin):

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

    def build(self, arch):
        container_name = f"krill-c-{arch}"

        arch_tuple = None
        if arch == "x86_64":
            pass
        elif arch in self.ARCH_MAP:
            arch_tuple = self.ARCH_MAP[arch]['tuple']
        else:
            raise ValueError("Unsupported arch")
        
        docker_file_content = DOCKER_TEMPLATE.replace("$TUPLE$", arch_tuple)

        self.build_container(docker_file_content, container_name)

