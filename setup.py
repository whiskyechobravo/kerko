#!/usr/bin/env python

import io
import re
from setuptools import setup, find_packages
from setuptools.command.install import install as BaseInstallCommand

with io.open('README.md', 'rt', encoding='utf8') as f:
    readme = f.read()

with io.open('kerko/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r"__version__ = '(.*?)'", f.read()).group(1)


class InstallCommand(BaseInstallCommand):

    def run(self):
        self.run_command('compile_catalog')  # Compile gettext MO files.
        super().run()


setup(
    name="Kerko",
    version=version,
    url="https://github.com/whiskyechobravo/kerko",
    project_urls={
        "Documentation": "https://github.com/whiskyechobravo/kerko",
        "Code": "https://github.com/whiskyechobravo/kerko",
        "Issue tracker": "https://github.com/whiskyechobravo/kerko/issues",
    },
    author="David Lesieur",
    author_email="kerko@whiskyechobravo.com",
    description="A Flask blueprint that provides a faceted search interface "
                "for bibliographies based on Zotero.",
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        "Babel>=2.6.0",
        "Bootstrap-Flask>=1.0.10",
        "environs>=4.0.0",
        "Flask>=1.0.2",
        "Flask-BabelEx>=0.9.3",
        "Flask-WTF>=0.14.2",
        "Jinja2>=2.10.1",
        "Pyzotero>=1.4.1",
        "Werkzeug>=0.15",
        "Whoosh>=2.7.4",
        "wrapt>=1.10.0",
        "WTForms>=2.2",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Database :: Front-Ends",
        "Topic :: Education",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        'flask.commands': ['kerko=kerko.cli:cli'],
    },
    message_extractors={
        'kerko': [
            ('**.py', 'python', None),
            ('**.jinja2', 'jinja2', {
                'extensions': 'jinja2.ext.autoescape, jinja2.ext.with_, jinja2.ext.do, jinja2.ext.i18n',
            })
        ]
    },
    cmdclass={
        'install': InstallCommand,
    }
)
