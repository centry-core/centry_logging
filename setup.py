#  Copyright (c) 2024 getcarrier.io
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

""" Package setup """

from setuptools import setup, find_packages

with open('requirements.txt', encoding='utf-8') as file:
    required = file.read().splitlines()

with open("version.txt", "r", encoding="utf-8") as f:
    version = f.read().splitlines()[0].strip()

setup(
    name='centry_logging',
    version=version,
    description='Centry logging core',
    long_description='Logging core for CentryCore/Pylon based apps',
    url='https://getcarrier.io',
    license='Apache License 2.0',
    author='getcarrier.io team',
    author_email='ivan_krakhmaliuk@epam.com, artem_rozumenko@epam.com',
    packages=find_packages(),
    install_requires=required
)
