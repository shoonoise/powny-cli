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
    setup(name='powny-cli',
          version='0.9.1',
          description='Powny command line tool',
          author='Alexander Kushnarev',
          author_email='avkushnarev@gmail.com',
          url='https://github.com/yandex-sysmon/powny-cli',
          packages=['pownycli'],
          package_data={'pownycli': ['config.yaml']},
          entry_points={'console_scripts': ['powny = pownycli.client:main']},
          install_requires=['powny>=1.0.0', 'pyyaml', 'click>=2', 'envoy-beta', 'requests',
                            'colorlog', 'colorama', 'tabloid'],
          tests_require=['vcrpy', 'pytest-cov'],
          cmdclass={'test': PyTest})
