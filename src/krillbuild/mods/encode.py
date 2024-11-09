from krillbuild.base import KrillPlugin

DOCKER_TEMPLATE=r"""FROM alpine:latest

RUN apk add -U coreutils xxd musl-utils

RUN echo -e '#!/bin/sh\nbase64 -w 0 $1 > $2\n' > /bin/base64file && \
    chmod +x /bin/base64file

RUN echo -e '#!/bin/sh\ncat $1 | iconv -f UTF8 -t UTF16LE | base64 > $2\n' > /bin/pwshbase64file && \
    chmod +x /bin/pwshbase64file

RUN echo -e '#!/bin/sh\nxxd -i $1 > $2\n' > /bin/cfile && \
    chmod +x /bin/cfile

WORKDIR /work

"""


class EncodePlugin(KrillPlugin):
    """Provides encoding functionality.
    
    """

    def get_image(self, arch):
        return f"krill-encode"
    
    def build(self, arch):
        
        docker_file_content = DOCKER_TEMPLATE

        self.build_container(docker_file_content, self.get_image(arch))

    def get_commands(self, arch):
        return ['base64', 'pwshbase64', 'cfile']
    
    def prepare_mod(self, arch, tool, infile, outfile, options):

        if outfile == infile and tool in ("base64", "pwshbase64"):
            outfile = outfile + ".base64"
        elif outfile == infile and tool == "cfile":
            outfile = outfile + ".h"
        command = tool
        if tool == "base64":
            command = "base64file"
        elif tool == "pwshbase64":
            command = "pwshbase64file"
        options = [infile, outfile] + options

        return command, outfile, {
            
        }, options