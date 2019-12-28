from setuptools import setup

setup(
   name='did',
   version='0.5.0',
   description='Did - command-line time tracking tool',
   author='Michał Czuczman',
   # author_email='',
   packages=['did'],
   install_requires=[],
   entry_points = {
        'console_scripts': ['did=did.did:main'],
   },
)
