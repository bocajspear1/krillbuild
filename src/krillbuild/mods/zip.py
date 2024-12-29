from krillbuild.base import KrillPlugin

DOCKER_TEMPLATE=r"""FROM alpine:latest

RUN apk add -U p7zip

RUN echo -e '#!/bin/sh\n7z a $2 $1 -tzip -mem=AES256 -p${3}' > /bin/aeszip && chmod +x /bin/aeszip
RUN echo -e '#!/bin/sh\n7z a $2 $1 -tzip -mem=ZipCrypto -p${3}' > /bin/cryptozip && chmod +x /bin/cryptozip

WORKDIR /work
"""


class ZIPPlugin(KrillPlugin):
    """Plugin for zipping files, utilizes 7z to support both ZipCrypto and AES encryption.
    
    """

    def get_image(self, arch):
        return f"krill-zip"
    
    def build(self, arch):
        
        docker_file_content = DOCKER_TEMPLATE

        self.build_container(docker_file_content, self.get_image(arch))

    def get_commands(self, arch):
        return ['7z']

    def prepare_mod(self, arch, tool, infile, outfile, options):
        command = tool
        options = [infile, outfile] + options

        print(options)

        return command, outfile, {
            
        }, options