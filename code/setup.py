# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

with open('requirements.txt') as f:
    install_requires = []
    for line in f.readlines():
        if not line.startswith('mock'):
            install_requires.append(line)

version = '${project.version}'

setup(
    name='nuvla-api',
    version=version,
    author="SixSq Sarl",
    author_email='support@sixsq.com',
    url='https://sixsq.com/nuvla',
    description="A wrapper to use Nuvla from Python programs.",
    keywords='nuvla devops api',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    namespace_packages=['nuvla'],
    zip_safe=False,
    license='Apache License, Version 2.0',
    include_package_data=True,
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development'
    ],
)
