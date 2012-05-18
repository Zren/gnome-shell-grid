gnome-shell-grid
================

This is a fork of paulswartz/gnome-shell-grid, with added support for
multiple monitors and multiple panels.

While I like many of the new features in
[GNOME Shell](http://live.gnome.org/GnomeShell), I missed the Grid plugin
from Compiz.  I liked getting to tile some windows without the overhead
of a tiling WM.  gnome-shell-grid runs in the background, listening for the
following keys:

* `C-M-S-u` or `C-M-KP_7` -- Top Left corner
* `C-M-S-k` or `C-M-KP_8` -- Top half
* `C-M-S-i` or `C-M-KP_9` -- Top Right corner
* `C-M-S-l` or `C-M-KP_6` -- Right half
* `C-M-S-m` or `C-M-KP_3` -- Bottom right corner
* `C-M-S-j` or `C-M-KP_2` -- Bottom half
* `C-M-S-n` or `C-M-KP_1` -- Bottom left corner
* `C-M-S-h` or `C-M-KP_4` -- Left half
* `C-M-KP_5` -- Full screen

To setup panels, edit Opts.panels.  The default is::

    panels = [
        {'top': 24, 'bottom': 24},  # monitor 0
        {'top': 24},                # monitor 1
    ]


How to Use
----------

### Prerequisites ###
#### Debian/Ubuntu #####

     sudo apt-get install python-xlib python-wnck

#### Fedora/Red Hat ####

     sudo yum install gnome-python2-libwnck python-xlib

#### gnome-shell-grid ####
     git clone git://github.com/acleone/gnome-shell-grid.git

### Running the daemon ###
     python gnome-shell-grid/gnome_shell_grid.py

License
-------

gnome-shell-grid is released under the GPLv3.  You can read the license in the
`LICENSE.txt` file.

Author
------

Original author:

I'm [Paul Swartz](http://paulswartz.net).  You can find me on Twitter
[@paulswartz](http://twitter.com/paulswartz) or on
[email](mailto:paulswartz+gnomeshellgrid@gmail.com).

Additional contributions from:

* Josh England
* Robert R. Meyer
* Alex Leone
