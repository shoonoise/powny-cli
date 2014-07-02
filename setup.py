#!/usr/bin/env python

from setuptools import setup

setup(name='gns-rules-checker',
      version='0.1',
      description='Tool to check GNS rules locally',
      author='Alexander Kushnarev',
      author_email='avkushnarev@gmail.com',
      url='https://github.com/yandex-sysmon/gns-rules-checker',
      packages=['gnsruleschecker'],
      package_data={'': ['config.yaml']},
      entry_points={'console_scripts': ['gns_checker = gnsruleschecker.checkrule:main']},
      requires=['gns'])
