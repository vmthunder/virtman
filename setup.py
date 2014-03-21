from setuptools import setup, find_packages
NAME="vmthunder"
DESCRIPTION="boot 1000 virtual machines in a minute"
AUTHOR="Ziyang Li"
AUTHOR_EMAIL="lzynudt@gmail.com"
URL="https://github.com/lihuiba/VMThunder"
setup(
    name=NAME,
    version="0.1",
    description=DESCRIPTION,
    long_description=open("README.md").read(),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license="GPL",
    url=URL,
    packages=find_packages(),
    #scripts = ["bin/fcg", "bin/fcg-easy"],
    keywords='vmthunder'
)
