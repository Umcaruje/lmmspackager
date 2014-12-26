#!/usr/bin/env python3

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://www.wtfpl.net/ for more details.


import sys
if sys.version_info < (3, 3):
    raise SystemExit('This needs Python 3.3 or newer')


import argparse

import os
import shutil
import subprocess
import zlib
import zipfile

import xml.dom.minidom

import tempfile


INSTRUMENTS = 'audiofileprocessor', 'sf2player'


ap = argparse.ArgumentParser(description='Package LMMS projects for easy sharing')
ap.add_argument('file')
ap.add_argument('--author')
ap.add_argument('--name')
ap.add_argument('--unpack', action='store_true')
args = ap.parse_args()
if not os.path.isfile(args.file):
    raise SystemExit('file {} not found'.format(args.file))


lmmsrc = os.path.join(os.path.expanduser('~'), '.lmmsrc.xml')
with xml.dom.minidom.parse(lmmsrc) as dom:
    paths = dom.getElementsByTagName('paths')[0]
    workingdir = paths.attributes['workingdir'].value


if not args.unpack:
    if args.file[-1:] == 'z':
        project = zlib.decompress(open(args.file, 'rb').read()[4:])
        outfilename = args.name + ".mmp" if args.name else os.path.basename(args.file)[:-1]
    else:
        project = open(args.file).read()
        outfilename = args.name + ".mmp" if args.name else os.path.basename(args.file)

        for encoding in 'latin-1', 'utf-8', 'ascii', None:
            try:
                project = project.encode(encoding).decode()
                break
            except UnicodeDecodeError:
                pass
            except TypeError:
                raise SystemExit("Unable to determine which encoding is used")


    validauthor = args.author not in ('.', '..', None)

    projectname = args.name if args.name else os.path.splitext(outfilename)[0]
    where = args.author if validauthor else projectname

    with tempfile.TemporaryDirectory() as tempdir:
        projectdir = os.path.join(tempdir, 'lmms', 'projects', where)
        sampledir = os.path.join(tempdir, 'lmms', 'samples', where)
        with xml.dom.minidom.parseString(project) as dom:
            ins = {}
            for i in INSTRUMENTS:
                ins[i] = []
                elements = dom.getElementsByTagName(i)
                files = [e.attributes['src'].value for e in elements]
                for f in files:
                    truths = (
                        os.path.join(workingdir, 'samples', f).startswith(workingdir),
                        os.path.isfile(os.path.join(workingdir, 'samples', f))
                    )
                    if not False in truths:
                        paths = os.path.join(workingdir, 'samples', f), os.path.join(sampledir, f)
                        ins[i].append(paths)
                        for e in elements:
                            if e.attributes['src'].value == f:
                                e.setAttribute('src', os.path.join(where, f))
                    else:
                        print("ignoring: {}".format(f))
            for i in ins:
                for source, target in set(ins[i]):
                    targetdir = os.path.dirname(target)
                    if not os.path.exists(targetdir):
                        os.makedirs(targetdir)
                    shutil.copyfile(source, target)
            if not os.path.exists(projectdir):
                os.makedirs(projectdir)
            with open(os.path.join(projectdir, outfilename), mode='a') as mmp:
                mmp.write(dom.toxml())
        shutil.make_archive('-'.join((where, projectname)) if validauthor else projectname, 'zip', tempdir, 'lmms')
else:
    home = os.path.abspath(os.path.join(workingdir, '..'))
    with zipfile.ZipFile(args.file) as z:
        equal, different = [], []
        for fname in z.namelist():
            file = os.path.join(home, fname)
            if os.path.exists(file):
                with open(file, 'rb') as f:
                    (equal if z.getinfo(fname).CRC == zlib.crc32(f.read()) else different).append(fname)
        if len(equal + different):
            if len(different):
                print('\nThe following files would be replaced by different ones:')
            for f in different:
                print(' ', f)

            if len(equal):
                print('\nThese files exist already and seem equal:')
            for f in equal:
                print(' ', f)
        if input('\nExtract and overwrite? [y/N] ').lower().startswith('y') or not len(equal + different):
            z.extractall(home)
        else:
            print('Giving up.')
