import pathlib

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):  # noqa: ARG002
        from babel.messages.frontend import compile_catalog

        cmd = compile_catalog()
        cmd.directory = pathlib.Path("src") / "kerko" / "translations"
        cmd.domain = "kerko"
        cmd.statistics = True
        cmd.finalize_options()
        cmd.run()
