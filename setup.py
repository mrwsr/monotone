"""
A monotonic clock using cffi's ABI mode.
"""

from setuptools import setup, find_packages


setup(
    use_incremental=True,
    name='monotone',
    url="https://github.com/mrwsr/monotone",
    description=__doc__,
    author="Mark Williams",
    author_email="shoprunner-pypi@shoprunner.com",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_pacakge_data=True,
    setup_requires=["cffi>=1.0.0", "incremental"],
    cffi_modules=["src/_build.py:ffibuilder"],
    install_requires=["cffi>=1.0.0", "incremental"],
    extras_require={
        'dev': ["coverage", "hypothesis>=3.6.1", "pytest"],
    },
    classifiers=[
        "Programming Language :: Python :: 2.7",
    ],
    license="MIT",
)
