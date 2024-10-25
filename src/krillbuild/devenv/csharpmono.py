from krillbuild.base import DevEnvBase

DOCKER_TEMPLATE=r"""FROM ubuntu:20.04

RUN apt-get -qq update \
&& DEBIAN_FRONTEND="noninteractive" apt-get -q install -y gnupg ca-certificates

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
RUN echo "deb https://download.mono-project.com/repo/ubuntu stable-focal main" | tee /etc/apt/sources.list.d/mono-official-stable.list
RUN apt-get -qq update \
&& DEBIAN_FRONTEND="noninteractive" apt-get -q install -y make mono-devel

RUN echo '#!/bin/sh\nmcs -lib:$LIBRARY_PATH "$@"\n' > /bin/crossmcs && \
    chmod +x /bin/crossmcs

RUN echo '#!/bin/sh\ncsc -lib:$LIBRARY_PATH "$@"\n' > /bin/crosscsc && \
    chmod +x /bin/crosscsc

RUN echo '#!/bin/sh\ngcs -lib:$LIBRARY_PATH "$@"\n' > /bin/crossgcs && \
    chmod +x /bin/crossgcs

RUN mkdir -p /work

WORKDIR /work
"""

class MonoDevEnvPlugin(DevEnvBase):


    TOOLS = {
        "mcs": "crossmcs",
        "csc": "crosscsc",
        "gsc": "crossgsc",
        "csharp": "csharp",
        "monodis": "monodis",
        "sn": "sn",
        "mkbundle": "mkbundle",
    }

    def get_image(self, arch):
        return f"krill-mono"

    def build(self, arch):
        container_name = self.get_image(arch)

        docker_file_content = DOCKER_TEMPLATE
        self.build_container(docker_file_content, container_name)

    def prepare_run(self, arch, tool, options):
        
        tool_command = ""

        all_tools = self.TOOLS
        
        if tool not in all_tools:
            tool_command = tool
        else:
            tool_template = all_tools[tool]
            tool_command = tool_template

        return tool_command, {
            # "LD_LIBRARY_PATH": f"/work/.krill/{arch}/lib",
            "LIBRARY_PATH": f"/work/.krill/{arch}/lib",
            "INSTALL_DIR": f"/work/.krill/{arch}",
        }, options

    def get_tools(self, arch):
        ret_commands = []

        for command in self.TOOLS:
            ret_commands.append(command)
        
        return ret_commands