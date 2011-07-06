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

## TO DO ##

- Create a settings file (in ~/.file_explorer?), to store...
	- path to adb
	- last used directory
- Empty directories are ignored when copying
- Drag and drop
	- to / from Nautilus
	- to / from same panel
	- between panels
- Local panel actions
- Find out host / device names
- Finer granularity when reporting the progress of copy operations. Right now it's too coarse!
