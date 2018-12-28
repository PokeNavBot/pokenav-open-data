import unittest
import os
from setuptools import setup, find_packages

VERSION_PATH = os.path.join(os.path.dirname(__file__), 'src', 'pokenav_data', 'VERSION')
VERSION = open(VERSION_PATH).read()


def my_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite


setup(name='pokenav-data',
      version=VERSION,
      description="Project containing consumers ",
      author='Daniel DeSousa',
      author_email='dan@pokenavbot.com',
      license='Public Domain',
      packages=find_packages("src"),
      package_dir={"": "src"},
      include_package_data=True,
      install_requires=[
        'requests>=2.20.0,<2.21.0',
        'google-cloud-bigquery>=1.7.0,<1.8.0',
      ],
      entry_points={
          'console_scripts': [
              'raid_reports_loader = pokenav_data.raid_reports_loader:main',
              'research_reports_loader = pokenav_data.research_reports_loader:main',
          ],
      },
      platforms='any',
      test_suite='setup.my_test_suite',
      classifiers=[
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
      ],
)
