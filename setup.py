#!/usr/bin/env python2.7

import sys
from distutils.core import setup

prefix=sys.prefix + '/bin'

setup(name='aafm',
      version='0.4',
      description='Android ADB File Manager',
      author='Soledad Penades',
      author_email='hello@soledadpenades.com',
      license='GPLv3',
      url='https://github.com/sole/aafm',
      packages=['aafm'],
      package_dir={'aafm': 'src'},
      package_data={'aafm': ['data/*/*']},
      data_files=[('/usr/share/icons/hicolor/32x32/apps', ['icon/32/aafm.png']),
                  ('/usr/share/icons/hicolor/48x48/apps', ['icon/48/aafm.png']),
                  ('/usr/share/icons/hicolor/64x64/apps', ['icon/64/aafm.png']),
                  ('/usr/share/icons/hicolor/128x128/apps', ['icon/128/aafm.png']),
                  ('/usr/share/icons/hicolor/256x256/apps', ['icon/256/aafm.png']),
                  ('/usr/share/icons/hicolor/scalable/apps', ['icon/scalable/aafm.svg']),
                  ('/usr/share/applications', ['aafm.desktop']),
                  (prefix , ['aafm'])]
      )
