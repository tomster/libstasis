from setuptools import setup


setup(
    version='0.3',
    name='stasis',
    packages=['stasis'],
    install_requires=[
        'dirtools',
        'pyramid'],
    entry_points={
        'console_scripts': [
            'stasis=stasis.cmd:main']})
