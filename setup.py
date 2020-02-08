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
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    keywords=["vapoursynth", "nazobase", "NAZOrip"]
)                                                               
