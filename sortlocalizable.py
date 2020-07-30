#!/usr/bin/python3
#
# sortlocalizable.py
# John Nimis 2020
# for WODHOPPER (Amagisoft)
#
# Called by my modified mergegenstrings.py
# Finds Localizable.strings files,
#   sorts each block of strings alphabetically by key
#   (delimited by empty lines or comments)
# Generates an xml file for import into Android strings.xml file
#   parent script (mergegenstrings.py) combines xml files and puts
#   them in correct directory hierarchy for Android
#

import sys
import os
import re
import datetime
from pathlib import Path

re_xml_val = re.compile(r"\"((?:[^\"\\]|\\.)*)\" = \"((?:[^\"\\]|\\.)*)\";")
re_autogen_comment = re.compile(r"\/\* Alphabetized on ")

argc = len(sys.argv)
if (argc != 2):
    print('Usage: %s [filename]' % sys.argv[0])
    quit()

filename = sys.argv[1]
if not os.path.isfile(filename):
    print('no file to sort found for %s' % filename)
    quit()

writepath = '%s.new' % filename

def cleanstringforxmlval(s):
    return s.replace("\n", "").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "\\\"")

def cleanstringforxmlkey(s):
    return s.replace("\n", "").replace("<", "").replace(">", "").replace("\"", "")

with open(filename, "r", errors='ignore') as ins:
    lines = []
    sortedLines = []
    xmlLines = []
    for line in ins:
        if line.startswith(("\"")):
            lines.append("%s" % line)

            # this is copy-paste code - also in sortuistrings.py
            # extract key; strip special characters
            xmlKeyRaw = cleanstringforxmlkey(re_xml_val.sub(r"\1", line))
            # make key lowercase and snakecase
            xmlKey = xmlKeyRaw.replace(" ","_").lower()

            # extract value of string
            xmlVal = cleanstringforxmlval(re_xml_val.sub(r"\2", line))
            xml = "  <string name=\"" + xmlKey + "\">" + xmlVal + "</string>\n"
            xmlLines.append(xml)
        elif len(lines) > 0:
            lines.sort()
            #print(lines)
            sortedLines.extend(lines)
            lines = []
        else:
            sortedLines.append(line)

    if len(lines) > 0:
        lines.sort()
        #print(lines)
        sortedLines.extend(lines)
        lines = []

    #print(sortedLines)

    if len(sortedLines) > 0:
        if re_autogen_comment.match(sortedLines[-1]):
            sortedLines.pop(-1)
        if not sortedLines[-1] in ('\n', '\r\n'):
            sortedLines.append('\n')
        sortedLines.append('/* Alphabetized on %s by sortlocalizable.py */\n' % (datetime.datetime.now()))
        with open(writepath, 'w') as filehandle:
            filehandle.writelines("%s" % place for place in sortedLines)

        # replace original file with new file

    if len(xmlLines) > 0:
        # create android xml file
        Path("xml").mkdir(parents=True, exist_ok=True)
        fn = os.path.basename(filename) # filename only, no other path components
        langcode = os.path.basename(os.path.dirname(filename))[: 2]
        xmlLines.insert(0, "\n  // Localizable.strings\n") # include comment with filename in Android strings.xml
        xmlwritepath = 'xml/%s-%s.xml' % (langcode, fn)
        with open(xmlwritepath, 'w') as filehandle:
            filehandle.writelines("%s\n" % place for place in xmlLines)
