"""
A monotonic clock using cffi's ABI mode.
"""

from setuptools import setup, find_packages


setup(
    name='monotone',
    version="17.0.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["src/_build.py:ffibuilder"],
    install_requires=["cffi>=1.0.0"],
)
