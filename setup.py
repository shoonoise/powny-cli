#!/usr/bin/env python

from setuptools import setup

setup(name='gns-cli',
      version='0.6',
      description='GNS Command line tool',
      author='Alexander Kushnarev',
      author_email='avkushnarev@gmail.com',
      url='https://github.com/yandex-sysmon/gns-rules-checker',
      packages=['gnscli'],
      package_data={'gnscli': ['config.yaml']},
      entry_points={'console_scripts': ['gns-cli = gnscli.client.cli']},
      install_requires=['gns', 'raava', 'pyyaml', 'click', 'envoy-beta', 'requests'])
