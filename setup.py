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
    extras_require={
        'dev': ["coverage", "hypothesis>=3.6.1", "pytest"],
    },
    classifiers=[
        "Programming Language :: Python :: 2.7",
    ],
    license="MIT",
)
