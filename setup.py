# Copyright (c) 2021 Cyb3rdog
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License in the file LICENSE.txt or at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
EscapePod Extension SDK:
    by cyb3rdog

For more information, please visit the project Github site: https://github.com/cyb3rdog/escapepod_python_sdk
It's powerful but easy to use, complex but not complicated, and versatile enough.

Requirements:
    * Python 3.6.1
    * Python 3.7
    * Python 3.8
    * Python 3.9
"""

import os.path
import sys
from setuptools import setup

if sys.version_info < (3, 6, 1):
    sys.exit('The EscapePod SDK requires Python 3.6.1 or later')

HERE = os.path.abspath(os.path.dirname(__file__))

def fetch_version():
    """Get the version from the package"""
    with open(os.path.join(HERE, 'escapepod_sdk', 'version.py')) as version_file:
        versions = {}
        exec(version_file.read(), versions)
        return versions

VERSION_DATA = fetch_version()
VERSION = VERSION_DATA['__version__']

def get_requirements():
    """Load the requirements from requirements.txt into a list"""
    reqs = []
    with open(os.path.join(HERE, 'requirements.txt')) as requirements_file:
        for line in requirements_file:
            reqs.append(line.strip())
    return reqs

setup(
    name='escapepod_sdk',
    version=VERSION,
    description="The EscapePod SDK for Cyb3rVector's EscapePod Extension Proxy",
    long_description=__doc__,
    url='https://github.com/cyb3rdog/escapepod_python_sdk',
    author='cyb3rdog',
    author_email='',
    license='Apache License, Version 2.0',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    zip_safe=True,
    keywords='anki ddl vector cyb3rvector robot escapepod extension proxy sdk python'.split(),
    packages=['escapepod_sdk', 'escapepod_sdk.messaging'],
    package_data={
        'escapepod_sdk': ['LICENSE.txt']
    },
    install_requires=get_requirements(),
    extras_require={
        'docs': ['sphinx', 'sphinx_rtd_theme', 'sphinx_autodoc_typehints'],
        'experimental': ['keras', 'scikit-learn', 'scipy', 'tensorflow'],
        'test': ['pytest', 'requests', 'requests_toolbelt'],
    }
)
