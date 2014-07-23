#!/usr/bin/env python

from setuptools import setup

setup(name='gns-rules-checker',
      version='0.5',
      description='Tool to check GNS rules locally',
      author='Alexander Kushnarev',
      author_email='avkushnarev@gmail.com',
      url='https://github.com/yandex-sysmon/gns-rules-checker',
      packages=['gnsruleschecker', 'gnscli'],
      package_data={'gnsruleschecker': ['config.yaml'], 'gnscli': ['config.yaml']},
      entry_points={'console_scripts': ['gns-checker = gnsruleschecker.checkrule:main',
                                        'gns-cli = gnscli.client.cli']},
      install_requires=['gns', 'raava', 'pyyaml', 'click', 'envoy-beta', 'requests'])
