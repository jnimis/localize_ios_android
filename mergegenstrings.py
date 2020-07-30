#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Localize.py - Incremental localization on XCode projects
# João Moreno 2009
# http://joaomoreno.com/

# Modified by Steve Streeting 2010 http://www.stevestreeting.com
# Changes
# - Use .strings files encoded as UTF-8
#   This is useful because Mercurial and Git treat UTF-16 as binary and can't
#   diff/merge them. For use on iPhone you can run an iconv script during build to
#   convert back to UTF-16 (Mac OS X will happily use UTF-8 .strings files).
# - Clean up .old and .new files once we're done

# Modified by Yoichi Tagaya 2015 http://github.com/yoichitgy
# Changes
# - Use command line arguments to execute as `mergegenstrings.py path routine`
#     path: Path to the directory containing source files and lproj directories.
#     routine: Routine argument for genstrings command specified with '-s' option.
# - Support both .swift and .m files.
# - Support .storyboard and .xib files.

# Modified by John Nimis 2020
# changes (related to integration into WODHOPPER)
# - translated to python3 (print statements and tab/space syntax)
# - Restricted to only storyboard and xib strings
# - sort each file alphabetically by key
# - create strings.xml files for each language for export to Android

from sys import argv
from codecs import open
from copy import copy
import os
import re
import glob

re_translation = re.compile(r'^"(.+)" = "(.+)";$')
re_comment_single = re.compile(r'^/\*.*\*/$')
re_comment_start = re.compile(r'^/\*.*$')
re_comment_end = re.compile(r'^.*\*/$')

class LocalizedString():
    def __init__(self, comments, translation):
        self.comments, self.translation = comments, translation
        self.key, self.value = re_translation.match(self.translation).groups()

    def __unicode__(self):
        return u'%s%s\n' % (u''.join(self.comments), self.translation)

class LocalizedFile():
    def __init__(self, fname=None, auto_read=False):
        self.fname = fname
        self.strings = []
        self.strings_d = {}

        if auto_read:
            self.read_from_file(fname)

    def read_from_file(self, fname=None):
        fname = self.fname if fname == None else fname
        try:
            f = open(fname, encoding='utf_8', mode='r', errors='ignore')
        except:
            print('File %s does not exist.' % fname)
            exit(-1)

        line = f.readline()
        while line:
            comments = [line]

            if not re_comment_single.match(line):
                while line and not re_comment_end.match(line):
                    line = f.readline()
                    comments.append(line)

            line = f.readline()
            if line and re_translation.match(line):
                translation = line
            else:
                continue

            line = f.readline()
            while line and line == u'\n':
                line = f.readline()

            string = LocalizedString(comments, translation)
            self.strings.append(string)
            self.strings_d[string.key] = string

        f.close()

    def save_to_file(self, fname=None):
        fname = self.fname if fname == None else fname
        try:
            f = open(fname, encoding='utf_8', mode='w')
        except:
            print('Couldn\'t open file %s.' % fname)
            exit(-1)

        for string in self.strings:
            f.write(string.__unicode__())

        f.close()

    def merge_with(self, new):
        merged = LocalizedFile()

        for string in new.strings:
            #print(string)
            if string.key in self.strings_d:
                new_string = copy(self.strings_d[string.key])
                new_string.comments = string.comments
                string = new_string

            merged.strings.append(string)
            merged.strings_d[string.key] = string

        return merged

def merge(merged_fname, old_fname, new_fname):
    try:
        old = LocalizedFile(old_fname, auto_read=True)
        new = LocalizedFile(new_fname, auto_read=True)

        #if os.path.isFile(merged):
        #    os.remove(merged)
        merged = old.merge_with(new)
        merged.save_to_file(merged_fname)
    except Exception as e:
        print('Error: %s' % str(e))

def is_empty_file(file):
    content = open(file, 'r', errors='ignore').read()
    if re.search(r'^\s*$', content):
        numBytes = os.stat(file).st_size
        #print("bytes: %s" % numBytes)
        #print("bytes < 2 is %s" % (numBytes < 2))
        return numBytes < 2 # this accounts for an ibtool bug that doesn't return an empty .strings file for an empty .storyboard

STRINGS_FILE = 'Localizable.strings'

def alphabetizeLocalizedStrings(path):
    print('Alphabetize localized strings...')
    languages = [lang for lang in [os.path.join(path, name) for name in os.listdir(path)]
                if lang.endswith('.lproj') and os.path.isdir(lang)]
    for language in languages:
        print(language)
        original = merged = os.path.join(language, STRINGS_FILE)
        old = original + '.old'
        new = original + '.new'

        if os.path.isfile(original):
            execpath = os.path.dirname(__file__)
            os.system('python3 %s/sortlocalizable.py %s' % (execpath, original))

            # copy new file, overwriting old Localizable.strings
            if os.path.isfile(new):
                os.rename(new, original)

def localizeCode(path, routine):
    print('Localize source code...')
    languages = [lang for lang in [os.path.join(path, name) for name in os.listdir(path)]
                if lang.endswith('.lproj') and os.path.isdir(lang)]
    for language in languages:
        print(language)
        original = merged = os.path.join(language, STRINGS_FILE)
        old = original + '.old'
        new = original + '.new'

        if os.path.isfile(original):
            os.rename(original, old)
            os.system('genstrings -q -s %s -o "%s" `find %s -name "*.swift" -o -name "*.m"`' % (routine, language, path))
            os.system('iconv -f UTF-16 -t UTF-8 "%s" > "%s"' % (original, new))
            merge(merged, old, new)
        else:
            os.system('genstrings -q -s %s -o "%s" `find %s -name "*.swift" -o -name "*.m"`' % (routine, language, path))
            os.rename(original, old)
            os.system('iconv -f UTF-16 -t UTF-8 "%s" > "%s"' % (old, original))

        if os.path.isfile(old):
            os.remove(old)
        if os.path.isfile(new):
            os.remove(new)

def organizeAndExportForAndroid(path, developmentLanguage):
    print("organizeAndExportXml...")
    baseDir = os.path.join(path, "Base.lproj")
    developmentLanguage = os.path.splitext(developmentLanguage)[0] + ".lproj" # Add the extension if not exists
    devlangcode = developmentLanguage[: 2]

    if os.path.isdir(baseDir):

        ibFileNames = [name for name in os.listdir(baseDir) if name.endswith('.storyboard') or name.endswith('.xib')]
        languages = [lang for lang in [os.path.join(path, name) for name in os.listdir(path)]
                    if lang.endswith('.lproj') and not lang.endswith('Base.lproj') and os.path.isdir(lang)]

        for language in languages:
            print(language)
            langcode = os.path.basename(language)[: 2]

            for ibFileName in ibFileNames:
                ibFilePath = os.path.join(baseDir, ibFileName)
                stringsFileName = os.path.splitext(ibFileName)[0] + ".strings"
                print('  ' + stringsFileName)
                fn = merged = os.path.join(language, stringsFileName)

                if os.path.isfile(fn):
                    # alphabetize strings file and generate xml for android
                    cwd = os.path.dirname(__file__)
                    os.system('python3 %s/sortuistrings.py %s' % (cwd, fn))

            # weave together xml files for this language - also convert Localizable.strings to xml


            xmldir = 'xml/%s-*.xml' % langcode # % os.path.dirname(cwd)
            if langcode == devlangcode:
                langcode = ""   # no suffix for development language
            else:
                langcode = "-%s" % langcode

            fileList = glob.glob(xmldir)
            #print(fileList)
            # filenames = ['file1.txt', 'file2.txt', 'file3.txt']
            dirname = 'xml/res/values%s' % langcode
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open('%s/strings.xml' % dirname, 'w') as outfile:
                for fname in fileList:
                    with open(fname) as infile:
                        outfile.write(infile.read())

        # clean up xml files
        xmlFilesToClean = glob.glob('xml/*.xml')
        for fileToClean in xmlFilesToClean:
            os.remove(fileToClean)

def localizeInterface(path, developmentLanguage):
    baseDir = os.path.join(path, "Base.lproj")
    developmentLanguage = os.path.splitext(developmentLanguage)[0] + ".lproj" # Add the extension if not exists
    if os.path.isdir(baseDir):
        print("Localize interface...")
        ibFileNames = [name for name in os.listdir(baseDir) if name.endswith('.storyboard') or name.endswith('.xib')]
        languages = [lang for lang in [os.path.join(path, name) for name in os.listdir(path)]
                    if lang.endswith('.lproj') and not lang.endswith('Base.lproj') and os.path.isdir(lang)]
        for language in languages:
            print(language)
            for ibFileName in ibFileNames:
                ibFilePath = os.path.join(baseDir, ibFileName)
                stringsFileName = os.path.splitext(ibFileName)[0] + ".strings"
                print('  ' + stringsFileName)
                original = merged = os.path.join(language, stringsFileName)
                old = original + '.old'
                new = original + '.new'

                if os.path.isfile(original) and not language.endswith(developmentLanguage):
                    os.rename(original, old)
                    os.system('ibtool --export-strings-file %s %s' % (original, ibFilePath))
                    os.system('iconv -f UTF-16 -t UTF-8 "%s" > "%s"' % (original, new))
                    merge(merged, old, new)
                else:
                    os.system('ibtool --export-strings-file %s %s' % (original, ibFilePath))
                    os.rename(original, old)
                    os.system('iconv -f UTF-16 -t UTF-8 "%s" > "%s"' % (old, original))

                if os.path.isfile(old):
                    os.remove(old)
                if os.path.isfile(new):
                    os.remove(new)


if __name__ == '__main__':
    argc = len(argv)
    if (argc <= 1 or 4 < argc):
        print('Usage: %s path_to_source_directory [routine] [development_language]' % argv[0])
        quit()

    path = os.path.abspath(argv[1])
    routine = argv[2] if argc > 2 else 'NSLocalizedString'
    developmentLanguage = argv[3] if argc > 3 else 'en'
    # localizeCode(path, routine) # this won't work with WH implementation of "".localized()
    localizeInterface(path, developmentLanguage)
    alphabetizeLocalizedStrings(path)
    organizeAndExportForAndroid(path, developmentLanguage)
