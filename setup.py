"""Setup."""

import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="machado",
    version="0.6.0",
    packages=find_packages(),
    include_package_data=True,
    license="GPL License",
    description="This library provides users with a framework to store, search and visualize biological data.",
    long_description=README,
    url="https://github.com/lmb-embrapa/machado",
    author="LMB",
    author_email="",
    classifiers=[
        "Environment :: Console",
        "Framework :: Django :: 5.2",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
    ],
    scripts=["bin/fixChadoModel.py"],
    install_requires=[
        "django~=5.2",
        "psycopg2-binary~=2.9.12",
        "networkx~=3.6",
        "obonet~=1.1.1",
        "biopython~=1.87",
        "tqdm~=4.67.3",
        "bibtexparser~=1.4.4",
        "djangorestframework~=3.15.2",
        "drf-yasg~=1.21.15",
        "drf-nested-routers~=0.95.0",
        "pysam~=0.24.0",
        "django-haystack~=3.3.0",
    ],
    zip_safe=False,
)
