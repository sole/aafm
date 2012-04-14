#!/usr/bin/env python2.7

import sys
from distutils.core import setup

prefix=sys.prefix + '/bin'

setup(name='aafm',
      version='0.4',
      description='Android filemanager, using adb.',
      author='Soledad Penades',
      author_email='hello@soledadpenades.com',
      license='GPLv3',
      url='https://github.com/sole/aafm',
      packages=['aafm'],
      package_dir={'aafm': 'src'},
      package_data={'aafm': ['data/*/*']},
      data_files=[('/usr/share/icons/highcolor/32x32', ['icon/32/aafm.png']),
                  ('/usr/share/icons/highcolor/48x48', ['icon/48/aafm.png']),
                  ('/usr/share/icons/highcolor/64x64', ['icon/64/aafm.png']),
                  ('/usr/share/icons/highcolor/128x128', ['icon/128/aafm.png']),
                  ('/usr/share/icons/highcolor/256x256', ['icon/256/aafm.png']),
                  ('/usr/share/icons/highcolor/scalable', ['icon/scalable/aafm.svg']),
                  ('/usr/share/applications', ['aafm.desktop']),
                  (prefix , ['aafm'])]
      )
