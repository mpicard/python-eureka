#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('HISTORY.rst') as f:
    history = f.read()

with open('requirements.txt') as f:
    install_requirements = f.read()

setup_requirements = [
    'pytest-runner',
]

test_requirements = [
    'pytest',
    'pytest-cov',
    'pytest-watch'
]

setup(
    name='python_eureka_client',
    version='0.0.1',
    description="Python based client for Netflix Eureka",
    long_description=readme + '\n\n' + history,
    author="Martin Picard",
    author_email='martin.picard@emc.com',
    url='https://github.com/mpicard/python_eureka_client',
    packages=find_packages(include=['eureka_client']),
    entry_points={
        'console_scripts': [
            'eureka=eureka_client.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=install_requirements,
    license="MIT license",
    zip_safe=False,
    keywords='',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
