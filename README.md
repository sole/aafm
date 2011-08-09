aafm
====

# Android ADB File Manager #

A command line + GUI (GTK based) Android ADB-based file manager

![Screenshot](http://sole.github.com/aafm/screenshot.png)

Recent Android releases (Honeycomb / 3.0+) replace the older USB mount protocol with the use of MTP (Massive Transfer Protocol). Unfortunately this is still very buggy and doesn't work as it should in any machine I have tested (and heard of): system slowing down to a halt when transferring large number of files, files which are there but cannot be seen by the computer... etc.

So I decided to go ahead and build a little utility that would if not fix, at least alleviate the pain of using Honeycomb devices. **aafm** uses ADB (one of the command line tools provided with the official Android SDK) for communicating with the Android device. This is the same method that IDEs implement.

## Installing ##

### Requirements ###

Python with PyGTK bindings, GTK, git, and the Android SDK

### Clone repository ###

Clone this repository to a place you fancy. For example, your Applications folder.

```git clone git://github.com/sole/aafm.git ~/Applications/aafm```

### Install the Android SDK ###

If it's not installed yet, download the SDK from its page and follow its instructions: http://developer.android.com/sdk/index.html

Basically (at least in Linux) just download a zip file and unpack it to a known location. In my case it's ```~/Applications/android-sdk-linux_86```. Once that is done, you need to make sure that the ADB tool is readily accessible from a shell (which is what **aafm** uses internally).

So to try that out, open a new terminal and type ```adb```. If it works, you should get a long help message that starts with something like ```Android Debug Bridge version 1.0.26```. If it doesn't work, you'll get something akin to ```adb: command not found```.

In case it doesn't work, you need to add the path to ADB to the environment PATH variable. In Linux this is done by editing a file called ```.bashrc``` in your home folder. Locate a line that looks like ```PATH=$PATH``` and make it look like this:

    PATH=$PATH:~/Applications/android-sdk-linux_86/platform-tools

The line above appends ADB's path to whatever value $PATH held before. The path might be different, according to wherever you've installed the Android SDK.

For more information on ADB and a list of its features, read over here: http://developer.android.com/guide/developing/tools/adb.html

Also, I haven't tried it myself, but it seems that it's possible to download and build a reduced subset of the Android SDK only, including ADB and a few more tools. This doesn't require Java installed in the system. This page describes how: http://lackingrhoticity.blogspot.com/2010/02/how-to-build-adb-android-debugger.html

### Close terminal and open it again ###

So the changes to the PATH get current.

### Configure udev rules (if in Linux) ###

You need to let the system know that when you connect your USB device (i.e. the tablet) it should allow you, as a non-root user, to access it. If you don't do that, you'll get a "Insufficient permissions for device" error.

This is done by adding a new file that contains so called udev rules.

For example, in Ubuntu 10.10 you would add a file in ```/etc/udev/rules.d/51-android.rules``` with the following content:

    # Samsung
    SUBSYSTEM=="usb", SYSFS{idVendor}=="04e8", MODE="0777"

Then change the file permissions:

    chmod a+r /etc/udev/rules.d/51-android.rules

To make sure it worked, connect the device and try to run ```adb devices``` in a terminal. If it's working properly, you should see a list more or less like this:

    List of devices attached 
    4342354131444B534652	device

The numbers aren't important, the important bit is that you see ```device``` instead of ```??????```.

If it isn't, you might need to either disconnect the device and try again, or reload udev so that the rules are actually loaded. Try with this:

    sudo /etc/init.d/udev restart

If everything else fails, try to log in and out again, or maybe even restart the system.

More information on udev rules and Android can be found on the official Android development guide: http://developer.android.com/guide/developing/device.html


### Enable Debug mode in the device ###

Go to _Settings → Applications → Development_ and make sure the USB debugging checkbox is ticked. You might get a scary warning saying debugging allows you to do nasty things--just ignore it.

### Execute aafm ###

To execute it, cd to the place where it's been cloned:

    cd ~/Applications/aafm/src/

And simply execute it:

    ./aafm-gui.py

If for some odd reason it has lost the executable permission, you can add it:

    chmod +x ./aafm-gui.py

Or simply execute it using Python:

    python ./aafm-gui.py

Once you're satisfied it's working, you can also make a launcher or add it to your Gnome menu, of course!

## Using it ##

If everything works (and why shouldn't it?) you should get a window divided in two panels. The left side represents your host computer, and initially should show the files of the aafm directory, since you launched it from there. The right side represents your Android device's files --so it needs to be connected to the computer, and _USB debugging_ must be enabled in the device.
You can navigate just as you would do with your favourite file explorer. Files can be dragged from one to another panel, directories created, and files renamed (hint: right click and explore the options the contextual menu offers you!). You can also drag from Nautilus (in GNOME) into the device panel, to copy files to the device, or drag _to_ Nautilus, for copying files from the device.

Be warned that currently the progress reporting is a bit hackish and with large files it will appear as if the window has got frozen. It hasn't--it's just waiting for the ADB transfer to finish. In the future this should be fixed, but I haven't come up with the best solution yet.


## License ##

Copyright (C) 2011 Soledad Penades (http://soledadpenades.com)

This software is licensed under a GPL V3 license. Please read the accompanying LICENSE.txt file for more details, but basically, if you modify this software and distribute it, you must make your changes public too, so that everyone can benefit from your work--just as you're doing with mine. 

You can also make your changes public even if you don't plan on redistributing this application, okay? Sharing is good! :-)


## Attributions ##

- Nice usability ideas from Mr.doob: http://mrdoob.com/
- FamFamFam icons: http://www.famfamfam.com/lab/icons/
- XDS with PyGTK tutorial from http://rodney.id.au/dev/gnome/an-xds-example


## Hacking ##

I'm by no means a GTK/Python/ADB/Android expert. I'm just learning so this project will surely contain many things that can be improved or that are plain wrong, so feel free to clone the repository and submit pull requests :-)

In order to make your life a bit easier I'll roughly show what each file does:

* **Aafm.py** - a class that communicates with an Android device, using ADB via shell commands. Takes care of copying and reading files, listing and parsing directories, etc.
* **aafm-gui.py** - this is the GTK front-end. Takes care of building the window with the host and device panels, and issuing instructions to Aafm when the user requests something to be done.
* **TreeViewFile.py** - a utility class that encapsulates a GTKTreeView and some more things in order to show file listings.
* **MultiDragTreeView.py** - an awesome class developed by the guys of Quod Libet, that allows more than one element of a TreeView to be selected and dragged around.

As you can see, an **aafm-cli.py** GUI counterpart is missing. There was one at the beginning but I didn't redo it when I rewrote most of the code from scratch. Feel free to... you know what, if you're interested in having a CLI version.

This has been developed in a Ubuntu Linux 10.10 system. I have no idea whether it'll work in other systems or not.


## TO DO ##

This is a public list of things I plan to do at some point. If you'd like some feature or think you've found a bug that is not in this list, please add it to the issue tracker at https://github.com/sole/aafm/issues

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
