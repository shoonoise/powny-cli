#!/usr/bin/env python

from setuptools import setup

setup(name='gns-rules-checker',
      version='0.2',
      description='Tool to check GNS rules locally',
      author='Alexander Kushnarev',
      author_email='avkushnarev@gmail.com',
      url='https://github.com/yandex-sysmon/gns-rules-checker',
      packages=['gnsruleschecker'],
      package_data={'gnsruleschecker': ['config.yaml']},
      entry_points={'console_scripts': ['gns_checker = gnsruleschecker.checkrule:main']},
      install_requires=['gns'])
