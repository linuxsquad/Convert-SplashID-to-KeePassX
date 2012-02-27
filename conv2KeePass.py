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

import sys
import csv
import time 
from time import gmtime, strftime

TODAY = strftime("%Y-%m-%dT%X",gmtime())

splashid_type = {}
splashid_value = []
splashid_type_prev = '0'
SPLASHID_2_KEEPASSX  = {'DESCRIPTION': 'title', 'COMPANY': 'title', 'USERNAME': 'username',
                        'PASSWORD': 'password', 'PIN': 'password', 'URL': 'url'}
xml_entry = {'title': [1,''], 'username': [2,''], 'url': [3,''], 'password': [4,''], 'notes': [5,''], 'uuid': [6,''], 'image': [7, '67'],
        'creationtime': [8,''], 'lastmodtime': [9,TODAY],'lastaccesstime': [91,TODAY] }
xml_group = {'title': ''}

if (len(sys.argv) > 1):
    splashid_export_f = sys.argv[1]
else:
    print "Please supply splashid_export_f name"
    quit(1)

with open(splashid_export_f, 'rb') as csv_file:
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

print '<?xml version="1.0" encoding="UTF-8"?>'
print "<pwlist>"

group_name_prev = ""

for single_record in splashid_value:
    if len(single_record) > 0:
        if  single_record[0] in splashid_type: 
            field_names = splashid_type[single_record[0]]

                    
            xml_entry['notes'][1] = ''

            for i, item in enumerate(field_names[1:-3]):
                j = i + 1
                try:
                    index = item.strip('0123456789 ').upper()
                    if index in SPLASHID_2_KEEPASSX :
                        if SPLASHID_2_KEEPASSX[index] == "title":
                            xml_entry[SPLASHID_2_KEEPASSX[index]][1] = single_record[j]+" ("+single_record[-2]+")"
                        else:
                            xml_entry[SPLASHID_2_KEEPASSX[index]][1] = single_record[j]
                    else:
                        xml_entry['notes'][1] += item+": "+single_record[j]+".\n"
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

            xml_entry['notes'][1] += "comment: "+single_record[-1]+"."
            
            print "  <pwentry>"
            print "     <group>{}</group>".format(field_names[0])

            for item in sorted( (value,field) for (field,value) in xml_entry.items() ):
                print "     <{0}>{1}</{0}>".format(item[1],item[0][1])
            print '     <expiretime expires="false">2999-12-28T23:59:59</expiretime>'
            print "  </pwentry>"
            
        else:
            print single_record, " Not Found"
    else:
        print single_record
    
print "</pwlist>"        
quit(0)