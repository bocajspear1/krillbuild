from krillbuild.base import KrillPlugin

DOCKER_TEMPLATE=r"""FROM alpine:latest

RUN apk add -U upx

WORKDIR /work

"""


class UPXPlugin(KrillPlugin):

    def build(self, arch):
        
        docker_file_content = DOCKER_TEMPLATE

        self.build_container(docker_file_content, "krill-upx")

    def prepare_mod(self, arch, filename, options):
        
        command = "upx"
        options = [filename] + options

        return "krill-upx", command, {
            
        }, options