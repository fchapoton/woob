#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright(C) 2010-2014 Christophe Benz, Laurent Bachelier
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import glob
import os
import subprocess
import sys
from distutils.cmd import Command
from distutils.log import WARN

from setuptools import find_packages, setup


class BuildQt(Command):
    description = 'build Qt applications'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.announce('Building Qt applications...', WARN)
        make = self.find_executable('make', ('gmake', 'make'))
        pyuic5 = self.find_executable('pyuic5', ('python2-pyuic5', 'pyuic5-python2.7', 'pyuic5'))
        if not pyuic5 or not make:
            print('Install missing component(s) (see above) or disable Qt applications (with --no-qt).',
                  file=sys.stderr)
            sys.exit(1)

        subprocess.check_call(
            [make,
             '-f', 'build.mk',
             '-s', '-j2',
             'all',
             'PYUIC=%s%s' % (pyuic5, ' WIN32=1' if sys.platform == 'win32' else '')])

    @staticmethod
    def find_executable(name, names):
        envname = '%s_EXECUTABLE' % name.upper()
        if os.getenv(envname):
            return os.getenv(envname)
        paths = os.getenv('PATH', os.defpath).split(os.pathsep)
        exts = os.getenv('PATHEXT', os.pathsep).split(os.pathsep)
        for name in names:
            for path in paths:
                for ext in exts:
                    fpath = os.path.join(path, name) + ext
                    if os.path.exists(fpath) and os.access(fpath, os.X_OK):
                        return fpath
        print('Could not find executable: %s' % name, file=sys.stderr)


def install_weboob():
    scripts = set(os.listdir('scripts'))
    packages = set(find_packages(exclude=['modules', 'modules.*']))

    qt_scripts = set(('qboobmsg',
                      'qhavedate',
                      'qgalleroob',
                      'qvideoob',
                      'weboob-config-qt',
                      'qwebcontentedit',
                      'qflatboob',
                      'qcineoob',
                      'qcookboob',
                      'qbooblyrics',
                      'qhandjoob'))

    if not options.qt:
        scripts = scripts - qt_scripts

    qt_packages = set((
        'weboob.applications.qboobmsg',
        'weboob.applications.qboobmsg.ui',
        'weboob.applications.qcineoob',
        'weboob.applications.qcineoob.ui',
        'weboob.applications.qcookboob',
        'weboob.applications.qcookboob.ui',
        'weboob.applications.qbooblyrics',
        'weboob.applications.qbooblyrics.ui',
        'weboob.applications.qhandjoob',
        'weboob.applications.qhandjoob.ui',
        'weboob.applications.qhavedate',
        'weboob.applications.qhavedate.ui',
        'weboob.applications.qvideoob',
        'weboob.applications.qvideoob.ui',
        'weboob.applications.qweboobcfg',
        'weboob.applications.qweboobcfg.ui',
        'weboob.applications.qwebcontentedit',
        'weboob.applications.qwebcontentedit.ui'
        'weboob.applications.qflatboob',
        'weboob.applications.qflatboob.ui',
        'weboob.applications.qgalleroob',
        'weboob.applications.qgalleroob.ui',
    ))

    if not options.qt:
        packages = packages - qt_packages

    data_files = [
        ('share/man/man1', glob.glob('man/*')),
    ]
    if options.xdg:
        data_files.extend([
            ('share/applications', glob.glob('desktop/*')),
            ('share/icons/hicolor/64x64/apps', glob.glob('icons/*')),
        ])

    # Do not put PyQt, it does not work properly.
    requirements = [
        'lxml',
        'cssselect',
        'requests>=2.0.0',
        'python-dateutil',
        'PyYAML',
        'html2text>=3.200',
        'six',
        'unidecode',
        'Pillow',
        'mechanize; python_version < "3.0"',
        'futures; python_version < "3.2"',
    ]

    try:
        if sys.argv[1] == 'requirements':
            print('\n'.join(requirements))
            sys.exit(0)
    except IndexError:
        pass

    setup(
        name='weboob',
        version='1.4',
        description='Weboob, Web Outside Of Browsers',
        long_description=open('README.md').read(),
        author='Romain Bignon',
        author_email='weboob@weboob.org',
        maintainer='Romain Bignon',
        maintainer_email='romain@weboob.org',
        url='http://weboob.org/',
        license='GNU AGPL 3',
        classifiers=[
            'Environment :: Console',
            'Environment :: X11 Applications :: Qt',
            'License :: OSI Approved :: GNU Affero General Public License v3',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python',
            'Topic :: Communications :: Email',
            'Topic :: Internet :: WWW/HTTP',
        ],

        packages=packages,
        scripts=[os.path.join('scripts', script) for script in scripts],
        data_files=data_files,

        install_requires=requirements,
        python_requires='>=2.7',
        tests_require=[
            'flake8',
            'nose',
            'xunitparser',
            'coverage',
        ],
        cmdclass={
            'build_qt': BuildQt,
        },
    )


class Options(object):
    qt = False
    xdg = True


options = Options()

if os.getenv('WEBOOB_SETUP'):
    args = os.getenv('WEBOOB_SETUP').split()
else:
    args = sys.argv[1:]
if '--qt' in args and '--no-qt' in args:
    print('--qt and --no-qt options are incompatible', file=sys.stderr)
    sys.exit(1)
if '--xdg' in args and '--no-xdg' in args:
    print('--xdg and --no-xdg options are incompatible', file=sys.stderr)
    sys.exit(1)

if '--qt' in args:
    options.qt = True
    args.remove('--qt')
elif '--no-qt' in args:
    options.qt = False
    args.remove('--no-qt')

if '--xdg' in args:
    options.xdg = True
    args.remove('--xdg')
elif '--no-xdg' in args:
    options.xdg = False
    args.remove('--no-xdg')


if options.qt:
    args.insert(0, 'build_qt')


sys.argv = [sys.argv[0]] + args

install_weboob()
