#!/usr/bin/env python
"""
Convert SplashID DB into Keepass XML v1.0

ASSUMPTION:
  keePass <Last Access> and <Last Modified> time stamp filled with a date and time of conversion
  SplashID <Description> and <Company> fields merge into keePassX <title>
  All SplashID fields that does not match main keePass ones, added to the keePass <notes>
  SplashID Creation Date is expected in the following format <November 28, 2009>
  
TODO:
  Some characters have to be replaced (for instance, &) since keePass refuses to import them
  If SplashID has no username, check <comment> section for <account> data to substitute

From KeePass website:

Important notes about the format:
 The files must be encoded using UTF-8 (Unicode). Other encodings are not supported.
 The following five entities must be encoded: < > & " '. They are encoded by &lt; &gt; &amp; &quot; &apos;.
 The UUID is a hex-encoded 16-byte string (i.e. an 32 ANSI hex character string in the XML file). It is unique (also across multiple databases) and can be used to identify entries.
 Dates/times are encoded in the standard date/time XML format (YYYY-MM-DDTHH:mm:ss): first the date in form YYYY-MM-DD, a 'T' character, and the time in form HH:mm:ss.

From SplashID website:
 You may also import and export SplashID records in CSV format.
 CSV stands for Comma Separated Values, and is a common file format
 readable by most spreadsheets, databases and word processors.
 If you wish to import a CSV file, the data must be in the following format:

    Type, Field 1, Field 2, Field 3, Field 4, Field 5, Field 6, Field 7, Field 8, Field 9, Date Modified, Notes, Category

 It is easy to create the above format in Excel by creating a spreadsheet
 with 13 columns (as designated above) with one record per row.
 Then save the splashid_export_f in CSV format.

 Note: When importing data, if the type field is blank the record
 will be placed in Unfiled. If there is a type name and it
 does not match an existing type a new type will be created.
"""

import codecs
import sys
import csv
import uuid
import string
from string import maketrans 
import time 
from time import gmtime, strftime

TODAY = strftime("%Y-%m-%dT%X",gmtime())
#
# NON-mutable
SPLASHID_2_KEEPASSX  = {'DESCRIPTION': 'title', 'COMPANY': 'title', 'USERNAME': 'username',
                        'PASSWORD': 'password', 'PIN': 'password', 'URL': 'url'}
CHAR_2_REPLACE = {'<': '&lt;', '>': '&gt;', '&': '&amp;','\"': '&quot;', '\'': '&apos;'}

#
# mutable
splashid_type = {}
splashid_value = []
splashid_type_prev = '0'
xml_entry = {'title': [1,''], 'username': [2,''], 'url': [3,''], 'password': [4,''], 'notes': [5,''], 'uuid': [6,''], 'image': [7, '0'],
        'creationtime': [8,''], 'lastmodtime': [9,TODAY],'lastaccesstime': [91,TODAY] }
xml_group = {'title': ''}

#
#
# 
if (len(sys.argv) > 1):
    splashid_export_f = sys.argv[1]
else:
    print "Please supply splashid_export_f name"
    quit(1)

#with codecs.open(splashid_export_f, "rb", "utf-8") as csv_file:
with open(splashid_export_f, "rb") as csv_file:
    csv_imported_splashid = csv.reader(csv_file)
    with open(splashid_export_f+".log", 'w') as log_file:
        for i, row in enumerate(csv_imported_splashid):
            csv_entry = [ item for item in row ]
            try:
                if csv_entry[0] == 'T':
                    try:
                        if csv_entry[1] in splashid_type:
                            pass
                        else:
                            splashid_type[csv_entry[1]] = csv_entry[2:]
                            log_file.write("  INFO: Group Name ="+csv_entry[2]+", Group ID ="+csv_entry[1]+"\n")
                        splashid_type_prev = csv_entry[1]
                    except IndexError, name:
                        pass
                if csv_entry[0] == 'F':
                    if csv_entry[1] != splashid_type_prev:
                        log_file.write("  WARN: Unrecognized Group ID F="+csv_entry[1]+", Guessing a correct one T="+splashid_type_prev+"\n")
                        csv_entry[1] = splashid_type_prev
                    splashid_value.append(csv_entry[1:])
            except IndexError, name:
                pass

splashid_value.sort()

def replace_character(string):
    mod_string = ""    
    for i,char in enumerate(string):
        if char in CHAR_2_REPLACE:
            mod_string += CHAR_2_REPLACE[char]
        else:
            mod_string += char
    return(mod_string)
            
print '<?xml version="1.0" encoding="UTF-8"?>'
print "<pwlist>"

group_name_prev = ""

for single_record in splashid_value:
    if len(single_record) > 0:
        if  single_record[0] in splashid_type: 
            field_names = splashid_type[single_record[0]]
#            print single_record
                    
            xml_entry['notes'][1] = ''

            for i, item in enumerate(field_names[1:-3]):
                j = i + 1
                try:
                    index = item.strip('0123456789 ').upper()
                    if index in SPLASHID_2_KEEPASSX :
                        if SPLASHID_2_KEEPASSX[index] == "title":
                            xml_entry[SPLASHID_2_KEEPASSX[index]][1] = '{!s} ({!s})'.format(single_record[j], single_record[-2])
                        else:
                            xml_entry[SPLASHID_2_KEEPASSX[index]][1] = single_record[j]
                    else:
                        xml_entry['notes'][1] += '{!s}: {!s}.\n'.format(item, repr(single_record[j]))
                except IndexError, name:
                    print "Index ERROR", name

            if single_record[10] != "":
                date_format = "%B %d, %Y"
                try:
                    time_tuple = time.strptime(single_record[10], date_format)
                    xml_entry['creationtime'][1] = strftime("%Y-%m-%dT%X", time_tuple)
                except TypeError, name:
                    print "  ERR: ", name
                    quit(1)

            xml_entry['notes'][1] += 'comment: {!s}.'.format(repr(single_record[-1]))
            
            print "  <pwentry>"
            print "     <group>{}</group>".format(field_names[0])

            for item in sorted( (value,field) for (field,value) in xml_entry.items() ):
                if item[1] is 'uuid':
                    print "     <{0}>{1}</{0}>".format(item[1],str(uuid.uuid1()).replace('-',''))
                else:                    
                    print "     <{0}>{1}</{0}>".format(item[1], replace_character(item[0][1]).encode("utf-8"))
            print '     <expiretime expires="false">2999-12-28T23:59:59</expiretime>'
            print "  </pwentry>"
            
        else:
            print single_record, " Not Found"
    else:
        print single_record
    
print "</pwlist>"        
quit(0)