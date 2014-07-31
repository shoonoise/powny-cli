#!/usr/bin/env python

from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


if __name__ == '__main__':
    setup(name='gnscli',
          version='0.6.1',
          description='GNS Command line tool',
          author='Alexander Kushnarev',
          author_email='avkushnarev@gmail.com',
          url='https://github.com/yandex-sysmon/gns-cli',
          packages=['gnscli'],
          package_data={'gnscli': ['config.yaml']},
          entry_points={'console_scripts': ['gns-cli = gnscli.client:main']},
          install_requires=['gns', 'raava', 'pyyaml', 'click', 'envoy-beta', 'requests', 'colorlog'],
          tests_require=['vcrpy', 'pytest-cov'],
          cmdclass={'test': PyTest})
