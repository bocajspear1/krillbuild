from krillbuild.compilers.muslbase import MuslBase

class ClangPlugin(MuslBase):

    COMPILER_NAME = "clang"

    def prepare_run(self, arch, options):
        container_name = f"krill-c-{arch}"

        return container_name, "crossclang", {
            # "LD_LIBRARY_PATH": f"/work/.krill/{arch}/lib",
            "LIBRARY_PATH": f"/work/.krill/{arch}/lib",
            "C_INCLUDE_PATH": f"/work/.krill/{arch}/include",
            "CPLUS_INCLUDE_PATH": f"/work/.krill/{arch}/include",
            "INSTALL_DIR": f"/work/.krill/{arch}",
        }, options