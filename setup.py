#############################################
# File Name: setup.py
# Author: WEN
# Created Time:  2019-05-01 00:00:00
#############################################

from setuptools import setup

setup(
    name            ='nazobase',
    version         ='0.1.13',
    py_modules      =['nazobase'],
    author          = 'WEN',
    license         = "LGPLv3",
    description     = "NAZOrip's basement",
    # install_requires=[
    #     '',
    # ],
    entry_points='''
        [console_scripts]
        nazobase=nazobase:nazobase
    ''',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
)