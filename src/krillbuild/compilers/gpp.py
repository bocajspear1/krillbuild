from krillbuild.compilers.muslbase import MuslBase

class GPPPlugin(MuslBase):

    COMPILER_NAME = "g++"

    def prepare_run(self, arch, options):
        container_name = f"krill-c-{arch}"

        return container_name, "crossg++", {
            # "LD_LIBRARY_PATH": f"/work/.krill/{arch}/lib",
            "LIBRARY_PATH": f"/work/.krill/{arch}/lib",
            "C_INCLUDE_PATH": f"/work/.krill/{arch}/include",
            "CPLUS_INCLUDE_PATH": f"/work/.krill/{arch}/include",
            "INSTALL_DIR": f"/work/.krill/{arch}",
        }, options