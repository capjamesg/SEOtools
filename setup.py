import setuptools
from setuptools import find_packages
import re

with open("./seotools/__init__.py", 'r') as f:
    content = f.read()
    # from https://www.py4u.net/discuss/139845
    version = re.search(r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content).group(1)
    
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="seotools",
    version=version,
    author="capjamesg",
    author_email="jamesg@jamesg.blog",
    description="A collection of tools for use with writing SEO-related programs in Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/capjamesg/seotools",
    install_requires=[
        "requests",
        "beautifulsoup4",
        "sentence-transformers",
        "networkx",
        "scikit-learn",
        "PyLD",
        "indieweb-utils"
    ],
    packages=find_packages(exclude=("tests",)),
    extras_require={
        "dev": ["flake8", "black==22.3.0", "isort", "twine", "pytest", "wheel"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
