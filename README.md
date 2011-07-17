aafm
====

# Android ADB File Manager #

A command line + GUI (GTK based) Android ADB-based file manager

The Android SDK must be installed in order for this to work.

## ADB? ##

If you don't want to be specifying the path to adb all the time, just add the path that contains its executable to your $PATH environment variable.
For example, edit .bashrc and add it like this:

	PATH=$PATH:~/Applications/android-sdk-linux_86/platform-tools

The line above appends adb's path to whatever value $PATH held before. The path might be different, according to wherever you've installed the Android SDK.

## Attributions ##

- Nice usability ideas from Mr.doob
- FamFamFam icons
- XDS with PyGTK tutorial from http://rodney.id.au/dev/gnome/an-xds-example

## TO DO ##

- Create a settings file (in ~/.file_explorer?), to store...
	- path to adb
	- last used directory
- Find out Android device name
- Finer granularity when reporting the progress of copy operations. Right now it's too coarse, and sometimes the window gets flagged as 'inactive' because it's not responding to the GTK loop (specially when copying huge files that take long or copying many files that take long too) (maybe use a queue...?)
- Allow to cancel operations
- Right click when there's nothing selected-> maybe it should select the row below (saves one extra click)
- Unify concepts: copy_to_device or copy_from_host? etc...
- Use file queue everywhere else it's not being used yet
- Refactor recursive operations in Aafm.py to simplify and debug them (specially the directories issues-should it create them or not?)
