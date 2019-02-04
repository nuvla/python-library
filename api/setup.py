# -*- coding: utf-8 -*-
import sys

from setuptools import find_packages, setup

with open('requirements.txt') as f:
    install_requires = []
    for line in f.readlines():
        if not line.startswith('mock'):
            install_requires.append(line)

if sys.version_info < (3, 2):
    install_requires.append('configparser')

version = '${project.version}'
packages = find_packages(where='src/')

setup(
    name='slipstream-api',
    version=version,
    author="SixSq Sarl",
    author_email='support@sixsq.com',
    url='http://sixsq.com/slipstream',
    description="A wrapper to use SlipStream from Python programs.",
    keywords='slipstream devops api',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    namespace_packages=['slipstream'],
    zip_safe=False,
    license='Apache License, Version 2.0',
    include_package_data=True,
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development'
    ],
)
