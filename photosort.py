#!/usr/bin/env python

import sys
import os
import shutil
import fnmatch
import hashlib
try:
    import EXIF
except:
    sys.stderr.write("You need to get EXIF.py. Try here: https://github.com/ianare/exif-py.")
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

def md5(f, block_size=2 ** 20):
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.digest()

def isBinaryDuplicate(srcPath, dstPath):
    srcF = open(srcPath, 'rb')
    dstF = open(dstPath, 'rb')
    return md5(srcF) == md5(dstF)

def getExifDate(path):
    try:
        f = open(path, 'rb')
        data = EXIF.process_file(f, details=False)
        f.close()
        if 'EXIF DateTimeOriginal' in data:
            year, month, day = data['EXIF DateTimeOriginal'].printable.split(' ')[0].split(':')
            return year, month, day
    except Exception, err:
        sys.stderr.write('ERROR in getExifDate: %s\n' % str(err))

    return None

def getDate(srcPath):
    return getExifDate(srcPath)

def getDupPath(dupBasePath, fileName):
    for i in range(1000):
        dupFileName = '.'.join(fileName.split('.')[:-1] + ['%s.jpg' % i])
        dupPath = os.path.join(dupBasePath, dupFileName)
        if not os.path.exists(dupPath):
            return dupPath
    sys.stderr.write('Too many dups of %s!\n', fileName)
    return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", help="Source directory to copy files from")
    parser.add_argument("target_directory", help="Target directory to copy files to")
    # Optional args
    parser.add_argument("-v", "--verbose", help="verbose output",
        action="store_true")
    parser.add_argument("-d", "--dryrun", help="do a dryrun without copying the files",
        action="store_true")

    args = parser.parse_args()
    sourceBasePath = os.path.abspath(args.source_directory)
    targetBasePath = os.path.abspath(args.target_directory)
    verbose = args.verbose
    dryrun = args.dryrun

    numFiles = 0
    numExactDups = 0
    numNonexactDups = 0
    numNodates = 0

    if verbose:
        print "Source directory: %s" % sourceBasePath
        print "Target directory: %s" % targetBasePath

    if targetBasePath.startswith(sourceBasePath):
        sys.stderr.write("ERROR: Target can't be in source. Exiting.\n")
        sys.exit(-1)

    for extension in ['*.jpg', '*.png', '*.mov', '*.avi']:
        for sourceFilePath in locate(extension, sourceBasePath):
            numFiles += 1

            if verbose:
                print '[%d] %s Exact dups: %d Non-exact dups: %d No date: %d' % (numFiles, sourceFilePath, numExactDups, numNonexactDups, numNodates)

            date = getDate(sourceFilePath)

            if date and len(date) ==3:
                # If we get a date from the metadata in the file, copy it to the
                # target dir under the subdir <year>/<month>/<day>/.
                if verbose:
                    print "Date for %s is %s" % (sourceFilePath, date)
                year, month, day = date
                targetFilePath = targetBasePath
                targetFilePath = os.path.join(targetFilePath, year)
                targetFilePath = os.path.join(targetFilePath, month)
                targetFilePath = os.path.join(targetFilePath, day)
                targetFilePath = os.path.join(targetFilePath, os.path.basename(sourceFilePath))
            else:
                # If we don't get a date from the metadata, preserve the
                # relative path of the file from the source dir in a 'no_date'
                # directory.
                relativePath = os.path.relpath(sourceFilePath, sourceBasePath)
                targetFilePath = os.path.join(targetBasePath, os.path.join('no_date', relativePath))
                numNodates += 1
                if verbose:
                    print "Unable to extract date for file %s" % sourceFilePath

            if os.path.exists(targetFilePath):
                # A file with the same name has already been copied to the
                # target tree. If the file is a binary duplicate, don't worry
                # about it. If not, copy it to a 'duplicates' dir.
                if isBinaryDuplicate(sourceFilePath, targetFilePath):
                    if verbose:
                        print "Exact duplicate found at %s" % sourceFilePath
                    numExactDups += 1
                    continue
                else:
                    targetFilePath = getDupPath(os.path.join(targetBasePath, 'duplicates'), os.path.basename(sourceFilePath))
                    if verbose:
                        print "Non-exact duplicate found at %s. Copying to %s." % (sourceFilePath, targetFilePath)
                    numNonexactDups += 1

            if verbose:
                print "Copying %s to %s" % (sourceFilePath, targetFilePath)

            # Make sure the target subdir exists.
            targetDirPath = os.path.dirname(targetFilePath)
            if not os.path.exists(targetDirPath) and not dryrun:
                if verbose:
                    print "Making target sub dir %s" % targetDirPath
                os.makedirs(targetDirPath)

            if not dryrun:
                while True:
                    try:
                        shutil.copyfile(sourceFilePath, targetFilePath)
                        break
                    except IOError:
                        sys.stderr.write('IOError on copy %s to %s.\n' % (sourceFilePath, targetFilePath))




