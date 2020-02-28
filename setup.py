from setuptools import setup, find_packages, Distribution

class BinaryDistribution(Distribution):
    """Distribution which always forces a binary package with platform name"""
    def has_ext_modules(foo):
        return True

with open("README.md", "r" ,encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name="nazobase", # Replace with your own username
    version="{{version_release}}",
    author="WEN",
    description="{{short_dscp}}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.nazorip.site",
    packages=find_packages(),
    package_data={
        'nazobase': ['nazolib.cp37-win_amd64.pyd'],
    },
    install_requires=['pymediainfo'],
    classifiers=[
        'Programming Language :: Python :: 3.7',
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires='>=3.7',
    keywords=["vapoursynth", "nazobase", "NAZOrip"]
)                                                               
