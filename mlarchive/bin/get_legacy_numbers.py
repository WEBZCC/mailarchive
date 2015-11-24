#!/usr/bin/python
'''
This script scans the MHonArc web archive, and creates a record in Legacy for each message
Based on pre-import.py, with changes for partial runs.  The Leagcy table will also be used
for redirecting requests to the old archive to the new one.
'''
# Set PYTHONPATH and load environment variables for standalone script -----------------
# for file living in project/bin/
import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not path in sys.path:
    sys.path.insert(0, path)

import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'mlarchive.settings.development'
django.setup()

# -------------------------------------------------------------------------------------

from mlarchive.archive.models import *
from email.utils import parseaddr
import argparse
import HTMLParser
import glob
import mailbox
import re
import warnings

NOIDPATTERN = re.compile(r'.*@NO-ID-FOUND.mhonarc.org')
PATTERN = re.compile(r'<!--X-Message-Id:\s+(.*)\s+-->')
PARSER = HTMLParser.HTMLParser()
MESSAGE_COUNT = 0
NOID = 0
MATCH_COUNT = 0
CREATED_COUNT = 0

def process_dirs(dirs,args):
    for dir in sorted(dirs):
        listname = dir.split('/')[-3]
        print "Importing %s" % listname
        files = glob.glob(dir + 'msg?????.html')
        process_files(listname,files,args)

def process_files(listname,files,args):
    for file in files:
        global MESSAGE_COUNT
        MESSAGE_COUNT += 1
        with open(file) as fp:
            msgid = get_msgid(fp)
            number = int(os.path.basename(file)[3:8])
            process_message(listname,msgid,number,args)

def process_message(listname,msgid,number,args):
    global MATCH_COUNT, CREATED_COUNT
    try:
        obj = Legacy.objects.get(msgid=msgid,email_list_id=listname)
        MATCH_COUNT += 1
        if obj.number != number:
            print 'mismatch: object:{}\t{} != {}'.format(obj.id,obj.number,number)
        elif args.verbose:
            print "found match {}:{}:{}".format(listname,msgid,number)
    except Legacy.DoesNotExist:
        CREATED_COUNT += 1
        if not args.check:
            #print 'creating record'
            Legacy.objects.create(msgid=msgid,email_list_id=listname,number=number)
        else:
            if args.verbose:
                print "would have created record {}:{}->{}".format(listname,msgid,number)

def get_msgid(fp):
    '''Returns msgid from MHonArc HTML message file'''
    global NOID
    for line in fp:
        if line.startswith('<!--X-Message-Id:'):
            match = PATTERN.match(line)
            if match:
                found = True
                msgid = match.groups()[0]
                # in msgNNNNN.html message-id's are escaped, need to unescape
                msgid = PARSER.unescape(msgid)
                if re.match(NOIDPATTERN,msgid):
                    NOID += 1
            else:
                raise Error('pattern failed (%s)' % fil)
            break
    u = unicode(msgid) # test for unknown encodings
    return msgid

def main():
    aparser = argparse.ArgumentParser(description='Scan archive for spam.')
    aparser.add_argument('list',nargs="?",default='*')     # positional argument
    aparser.add_argument('-v','--verbose', help='verbose output',action='store_true')
    aparser.add_argument('-c','--check',help="check only, dont't import",action='store_true')
    aparser.add_argument('--file',type=str)
    args = aparser.parse_args()
    
    if args.check:
        print "Check only..."

    if args.file:
        # import one file only
        print "Processing File {}".format(args.file)
        listname = args.file.split('/')[-3]
        process_files(listname,[args.file],args)

    else:
        # scan full archive or one list
        pattern = '/a/www/ietf-mail-archive/web*/{}/current/'.format(args.list)
        dirs = glob.glob(pattern)
        process_dirs(dirs,args)

    #print "Errors: %d" % errors
    print "message_count: %d" % MESSAGE_COUNT
    print "match_count: %d" % MATCH_COUNT
    print "created_count: %d" % CREATED_COUNT
    print "NO IDs: %d" % NOID

if __name__ == "__main__":
    main()