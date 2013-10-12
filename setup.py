from setuptools import setup


setup(
    version='0.1',
    name='stasis',
    packages=['stasis'],
    install_requires=[
        'pyramid'],
    entry_points={
        'console_scripts': [
            'stasis=stasis.cmd:main']})
