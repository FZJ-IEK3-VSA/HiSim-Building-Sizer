#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("requirements.txt") as requirements_file:
    requirements = requirements_file.read().splitlines()

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest>=3"]


setup(
    author="David Neuroth",
    author_email="d.neuroth@fz-juelich.de",
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="The Building Sizer optimizes household infrastructure components in HiSim.",
    long_description=readme,
    install_requires=requirements,
    license="MIT license",
    include_package_data=True,
    keywords="building Sizer",
    name="building_sizer",
    packages=find_packages(include=["building_sizer", "building_sizer.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/audreyr/hisim",
    version="0.1.0",
    zip_safe=False,
)
