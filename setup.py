# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

PACKAGE_NAME = 'thd74tool'
PACKAGE_VERSION = '0.0.1a1'

INSTALL_REQUIRES = [
    'coloredlogs',
    'ipython',
    'pyserial'
]

TESTS_REQUIRE = [
    'coverage',
    'pycodestyle',
    'pytest',
    'pytest-pycodestyle',
    'pytest-runner'
]

DEV_REQUIRES = [
    'pylint',
    'rope'
] + TESTS_REQUIRE

setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VERSION,
    description='Tool for Kennwod TH-D74 series radio flashing and configuration',
    classifiers=[
        'Environment :: Console',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Customer Service',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Communications :: Ham Radio'
    ],
    keywords=['hamradio', 'radio', 'kenwood', 'thd74', 'firmware', 'flashing'],
    author='Christiane Ruetten',
    author_email='cr@23bit.net',
    url='https://github.com/cr/thd74',
    download_url='https://github.com/cr/thd74/archive/master.tar.gz',
    license='GPLv3',
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,  # See MANIFEST.in
    zip_safe=True,
    use_2to3=False,
    install_requires=INSTALL_REQUIRES,
    tests_require=TESTS_REQUIRE,
    extras_require={'dev': DEV_REQUIRES},  # For `pip install -e .[dev]`
    entry_points={
        'console_scripts': [
            'thd74tool = thd74tool.main:main'
        ]
    }
)
