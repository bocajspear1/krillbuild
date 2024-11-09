from krillbuild.base import KrillPlugin

DOCKER_TEMPLATE=r"""FROM alpine:latest

RUN apk add -U upx

WORKDIR /work

"""


class UPXPlugin(KrillPlugin):

    def get_image(self, arch):
        return f"krill-upx"
    
    def build(self, arch):
        
        docker_file_content = DOCKER_TEMPLATE

        self.build_container(docker_file_content, self.get_image(arch))

    def get_commands(self, arch):
        return ['upx']

    def prepare_mod(self, arch, tool, infile, outfile, filename, options):
        command = "upx"
        options = [filename] + options

        return command, outfile, {
            
        }, options