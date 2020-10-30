#!/usr/bin/env python

"""
Package build setup script.

Metadata and options are specified in `setup.cfg`.

Reference: https://setuptools.readthedocs.io/en/latest/setuptools.html
"""

import setuptools
from setuptools.command.develop import develop as BaseDevelop
from setuptools.command.sdist import sdist as BaseSDist
try:
    from wheel.bdist_wheel import bdist_wheel as BaseBDistWheel
except ImportError:
    BaseBDistWheel = None


class CompileCatalogMixin():
    """
    Compile MO files with Babel's ``compile_catalog`` command.

    This happens after installing in development mode, or before building sdist
    and wheel.
    """

    # Note: Inspired by WTForms' setup.py.

    def run(self):
        is_develop = isinstance(self, Develop)

        if not is_develop:
            self.run_command('compile_catalog')

        super().run()

        if is_develop and not self.uninstall:
            self.run_command('compile_catalog')


class Develop(CompileCatalogMixin, BaseDevelop):
    pass


class SDist(CompileCatalogMixin, BaseSDist):
    pass


cmd_classes = {
    'develop': Develop,
    'sdist': SDist,
}

if BaseBDistWheel:

    class BDistWheel(CompileCatalogMixin, BaseBDistWheel):
        pass

    cmd_classes['bdist_wheel'] = BDistWheel


if __name__ == "__main__":
    setuptools.setup(cmdclass=cmd_classes)
