from krillbuild.base import KrillPlugin

DOCKER_TEMPLATE=r"""FROM alpine:latest

RUN apk add -U cmake make musl-dev gcc g++ git python3

RUN git clone https://github.com/GunshipPenguin/kiteshield.git /opt/kiteshield

WORKDIR /opt/kiteshield

RUN git submodule update --init && \
    cd packer/bddisasm && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make

RUN sed -i 's/-Wall -Werror//' packer/Makefile && sed -i 's/-Wall -Werror//' loader/Makefile && \ 
    make

RUN ln -s /opt/kiteshield/packer/kiteshield /bin/kiteshield

WORKDIR /work

"""


class KiteshieldPlugin(KrillPlugin):
    """Plugin for the Kiteshield, a x64-86 encryptor
    
    """

    def get_image(self, arch):
        return f"krill-kiteshield-{arch}"
    
    def build(self, arch):

        if arch != "x86_64":
            raise ValueError("Mod does not support non-x86_64")
        
        docker_file_content = DOCKER_TEMPLATE

        self.build_container(docker_file_content, self.get_image(arch))

    def get_commands(self, arch):
        return ['kiteshield']
    
    def prepare_mod(self, arch, tool, filename, options):
        command = "kiteshield"
        options = [filename] + options

        return command, {
            
        }, options