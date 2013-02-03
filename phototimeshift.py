#!/usr/bin/env python

import sys
import os
import datetime
import fnmatch

try:
    import pyexiv2
except:
    sys.stderr.write("\nYou need to get pyexiv2.\n\n")
    sys.stderr.write("This is currently a pain on the Mac. I got it to work with:\n")
    sys.stderr.write("  brew install python --universal\n")
    sys.stderr.write("  brew install boost --universal\n")
    sys.stderr.write("  brew install pyexiv2\n\n")
    sys.exit(-1)

def insensitive_pattern(pattern):
    def either(c):
        return '[%s%s]' %(c.lower(), c.upper()) if c.isalpha() else c
    return ''.join(map(either, pattern))

def locate(pattern, root=os.getcwd()):
    pattern = insensitive_pattern(pattern)
    for path, dirs, files in os.walk(root):
        for filename in [os.path.abspath(os.path.join(path, filename)) for
                         filename in files if
                         fnmatch.fnmatch(filename, pattern)]:
            yield filename

def getDate(srcPath):
    try:
        metadata = pyexiv2.ImageMetadata(srcPath)
        metadata.read()
        tag = metadata['Exif.Photo.DateTimeOriginal']
        return tag.value
    except Exception, err:
        sys.stderr.write('ERROR in getDate: %s\n' % str(err))
        return None

def setDate(srcPath, date):
    try:
        metadata = pyexiv2.ImageMetadata(srcPath)
        metadata.read()
        tag = metadata['Exif.Photo.DateTimeOriginal']
        tag.value = date
        tag = metadata['Exif.Photo.DateTimeDigitized']
        tag.value = date
        metadata.write()
    except Exception, err:
        sys.stderr.write('ERROR in getDate: %s\n' % str(err))
        return None



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", help="Source directory to copy files from")
    # Optional args
    parser.add_argument("-f", "--from-date", help="date to shift from in YYYY-MM-DD")
    parser.add_argument("-t", "--to-date", help="date to shift to in YYYY-MM-DD")
    parser.add_argument("-s", "--shift-days", help="days to shift the dates")
    parser.add_argument("-v", "--verbose", help="verbose output",
        action="store_true")
    parser.add_argument("-d", "--dryrun", help="do a dryrun without copying the files",
        action="store_true")


    args = parser.parse_args()

    sourceBasePath = os.path.abspath(args.source_directory)
    shift_days = args.shift_days
    from_date = args.from_date
    to_date = args.to_date

    numFiles = 0

    if shift_days:
        timedelta = datetime.timedelta(days=int(shift_days))
    else:
        try:
            from_year, from_month, from_day = args.from_date.split('-')
            to_year, to_month, to_day = args.to_date.split('-')
            timedelta = datetime.datetime(int(to_year), int(to_month), int(to_day)) - datetime.datetime(int(from_year), int(from_month), int(from_day))
        except:
            sys.exit(-1)

    verbose = args.verbose
    dryrun = args.dryrun

    if verbose:
        print "Source directory: %s" % sourceBasePath

    for extension in ['*.jpg', '*.png', '*.mov', '*.avi']:
        for sourceFilePath in locate(extension, sourceBasePath):
            numFiles += 1

            fromDate = getDate(sourceFilePath)

            if fromDate:
                toDate = fromDate + timedelta

                if verbose:
                    print "[%d] %s changing date from %s to %s" % (numFiles, sourceFilePath, fromDate, toDate)

                if not dryrun:
                    setDate(sourceFilePath, toDate)
            else:
                if verbose:
                    print "Skipping %s because it has do date metadata." % sourceFilePath






