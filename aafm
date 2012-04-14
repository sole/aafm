#!/bin/sh

executable=""
site_path=""

#Check the correct name for python2 interpreter, assume no one uses in distro with python
#version lower than 2.5.0

which python > /dev/null 2>&1
if [ "$?" == "0" ]; then
	version=$(python -c 'import sys; print(sys.version[:1])')
	if [ "$version" = "2" ]; then
		executable=python
	fi
fi

which python2 > /dev/null 2>&1
if [ "$?" = "0" ]; then
	executable=python2
fi

which python2.5 > /dev/null 2>&1
if [ "$?" = "0" ]; then
	executable=python2.5
fi

which python2.6 > /dev/null 2>&1
if [ "$?" = "0" ]; then
	executable=python2.6
fi

which python2.7 > /dev/null 2>&1
if [ "$?" = "0" ]; then
	executable=python2.7

else
	if [ "$executable" = "" ]; then
		echo "Could not find the python executable to run the application with."
		echo "Please enter the python 2 interpreter executable's name or press enter to exit"
		read executable
		if [ "$executable" = "" ]; then
			echo "Please install a python2 interpreter and try again. Exiting!"
			exit 1
		fi
	fi
fi

#Assume we have actually installed aafm to the site-packages dir....
site_path="$($executable -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")"

#Launch Aafm from site-packages path and pass any arguments given
$executable "${site_path}/aafm/aafm-gui.py" "$@"

