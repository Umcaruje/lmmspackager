lmmspackager
============

This is a crude Python script that should package LMMS projects with the
samples it uses, in a zip archive.

Requirements:
* Python 3.3 or later
* LMMS

Known bugs:
* Because I have no access to Windows, I don't have any idea how this works
  there. Feel free to fork and fix.
* If the filename of a compressed project contains unicode characters, LMMS
  will refuse to decompress it and instead claim that the file is corrupted.
  (This is a bug with LMMS, not lmmspackager.)

TODO:
* Support for sample tracks
* Supports for samples outside LMMS working directory
