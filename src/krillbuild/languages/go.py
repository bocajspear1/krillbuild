from krillbuild.base import KrillPlugin

DOCKER_TEMPLATE=r"""FROM alpine:latest

RUN apk add -U wget gcc

RUN wget https://go.dev/dl/go1.23.1.linux-amd64.tar.gz -O go.tar.gz && \
tar -C /usr/local -zxf go.tar.gz && \
rm go.tar.gz

RUN mkdir -p /opt/toolchain && \
wget https://github.com/bocajspear1/static-toolchains/releases/download/latest/$TUPLE$-musl-toolchain.tar.gz  -O /tmp/toolchain.tar.gz && \
tar -zxvf /tmp/toolchain.tar.gz -C /opt/toolchain && \
rm /tmp/toolchain.tar.gz

RUN ln -s /opt/toolchain/bin/$TUPLE$-gcc /bin/crossgcc 

RUN rmdir /usr/local/bin && ln -s /usr/local/go/bin /usr/local/bin

RUN mkdir -p /work

WORKDIR /work
"""

class GoPlugin(KrillPlugin):

    def build(self, arch):
        container_name = f"krill-go-{arch}"
        if arch == "powerpc":
            raise ValueError("Powerpc not supported by Go!")
        elif arch == "arm":
            arch_tuple = "arm-linux-musleabi"
        elif arch == "mipsel":
            arch_tuple = "mipsel-linux-musl"
        else:
            raise ValueError("Unsupported arch")
        
        docker_file_content = DOCKER_TEMPLATE.replace("$TUPLE$", arch_tuple)

        self.build_container(docker_file_content, container_name)


    def prepare_compile(self, arch, options):

        container = "UNKNOWN"
        
        if arch == "mipsel":
            arch = "mipsle"
            container = "krill-go-mipsel"
        elif arch == "arm":
            container = "krill-go-arm"
        elif arch in ('powerpc',):
            return None, None, None, None
        # elif arch == "mipsel":
        #     arch = f"krill-c-mipsel"
        # elif arch == "powerpc":
        #     arch = f"krill-c-powerpc"

        return container, "go", {
            "GOOS": "linux",
            "GOARCH": arch,
            "CC": "crossgcc"
        }, options