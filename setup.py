#! /usr/bin/env python

from setuptools import setup

setup(
    name='prm-package-server',
    version='0.0.1',
    description=' API to query prm package and module specifications',
    keywords='project management ',
    license='GPLv3',
    packages=['prmpckgsrv'],
    package_data={'': ['LICENSE']},
    install_requires=[
        'Flask >= "0.12"',
        'flask-cors >= "3.0.2"',
        'pyaml'
    ]
)
