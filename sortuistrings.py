#!/usr/bin/python3
#
# sortuistrings.py
# John Nimis 2020
# for WODHOPPER (Amagisoft)
#
# Called by my modified mergegenstrings.py
# Sorts generated .strings file for a UI compoenent by localization key
# Generates an xml file for import into Android strings.xml file
#   parent script (mergegenstrings.py) combines xml files and puts
#   them in correct directory hierarchy for Android
#

import sys
import re
import datetime
import os
from re import compile
from pathlib import Path

argc = len(sys.argv)
if (argc != 2):
    print('Usage: %s [filename]' % sys.argv[0])
    quit()

re_sortkey = compile(r'(\/\* Class = "[^"]+";[^"]+"((?:[^"\\]|\\.)*)".+)$')
re_remove_sortkey = compile(r'^(.+)\[\*\*\*SORTKEY\*\*\*\]')
re_extract_sortkey = compile(r'^(.+)\[\*\*\*SORTKEY\*\*\*\].+')
re_remove_newlinekey = compile(r'\[\*\*\*LINEBREAK\*\*\*\]')
re_xml_val = compile(r"\"(?:[^\"\\]|\\.)*\" = \"((?:[^\"\\]|\\.)*)\";")

filepath = sys.argv[1]
langdirectory = os.path.dirname(filepath)
langcode = os.path.basename(langdirectory)[: 2]
filename = os.path.basename(os.path.normpath(filepath))

def cleanstringforxmlval(s):
    return s.replace("\n", "").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "\\\"")

def cleanstringforxmlkey(s):
    return s.replace("\n", "").replace("<", "").replace(">", "").replace("\"", "")

#print("filepath: %s" % filepath)

with open(filepath, "r", errors='ignore') as ins:
    lines = []
    xmlLines = []
    thisline = ""
    for line in ins:
        if line.startswith(("/*")):
            thisline = re_sortkey.sub(r"\2[***SORTKEY***]\1[***LINEBREAK***]", line).replace("\n", "")
        elif line.startswith("\""):
            if thisline == "":
                print("data is not in correct format: make sure .strings file is pairs of lines")

            # this is copy-paste code - also in sortlocalizable.py
            # generate xml for Android HERE
            # extract key; strip special characters
            xmlKeyRaw = re.sub('[^A-Za-z0-9\s]+', '', re_extract_sortkey.sub(r"\1", thisline))
            # make key lowercase and snakecase
            xmlKey = cleanstringforxmlkey(xmlKeyRaw.replace(" ","_").lower())
            # extract value of string
            xmlVal = cleanstringforxmlval(re_xml_val.sub(r"\1", line))
            xml = "  <string name=\"" + xmlKey + "\">" + xmlVal + "</string>\n"
            xmlLines.append(xml)

            # print(xmlKey + ": " + xmlVal)
            thisline = thisline + line
            lines.append(thisline)
            thisline = ""
        else:
            if thisline != "":
                print("data is not in correct format: make sure .strings file is pairs of lines")
                # fatal error? need to warn, at least

    # sort alphabetically
    lines.sort(key=lambda v: v.upper())
    xmlLines.sort(key=lambda v: v.upper())

    # now we need to remove the sort key and reformat the .strings file
    resultlines = []
    for line in lines:
        res = re_remove_sortkey.sub(r"", line)
        resLine = re_remove_newlinekey.sub(r"\n", res)
        resultlines.append(resLine)

    writefilename = '%s.new' % filename
    writepath = os.path.join(langdirectory, writefilename)

    if len(resultlines) > 0:
        #print(*resultlines, end = "", sep = "")
        resultlines.insert(0, '/* Autogenerated on %s by sortuistrings.py */\n' % (datetime.datetime.now()))
        with open(writepath, 'w') as filehandle:
            filehandle.writelines("%s\n" % place for place in resultlines)
        # this will replace the original file with the alphabetized one
        os.rename(writepath, filepath)
    if len(xmlLines) > 0:
        #print(*xmlLines, end = "", sep = "")
        Path("xml").mkdir(parents=True, exist_ok=True)
        xmlwritepath = 'xml/%s-%s.xml' % (langcode, filename)
        xmlLines.insert(0, "\n  // %s\n" % filename) # include comment with filename in Android strings.xml
        with open(xmlwritepath, 'w') as filehandle:
            filehandle.writelines("%s\n" % place for place in xmlLines)
