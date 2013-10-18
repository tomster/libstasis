from setuptools import setup


setup(
    version='0.3',
    name='libstasis',
    packages=['libstasis'],
    install_requires=[
        'propdict>1.1',
        'dirtools',
        'sqlalchemy',
        'zope.interface'])
