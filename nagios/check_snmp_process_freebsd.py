#!/usr/bin/env python
#################################################### 
##  ___   ____       ____   ___  ## cs.huji.ac.il ##
## |   | /   /       \   \ |   | ##    /\         ##
## |   |/   /         \   \|   | ##   / /         ##
## |       /       __  \       | ##   \_/         ##
## |      /   ___ |  |_ \      | ##    _          ##
## |      \  / _ \|   _|/      | ##   | |  __  _  ##
## |       \/ / \ \  | /       | ##   | | /  \//  ##
## |   |\   \ \_/ /  |/   /|   | ##   | |/ /\ \   ##
## |___| \___\___/\__/___/ |___| ##   \_  /  \_\  ##
##      KeeperoftheKeys.nl       ##    /_/        ## 
####################################################

###############################################################################
# Written by E.S. Rosenberg 5774/2014
#
# This script will query a SNMP Table and see if one of the values in the table
# matches the search string, at HUJI its' initial use will be to determine if
# processes are running on FreeBSD hosts, undoubtedly other uses will be found
# in the future.
#
# Please pass --help to see usage instructions.
#
# This script requires PySNMP.
# If PySNMP is not installed in the "main" python environment create a virtual
# python environment and install pysnmp inside of it:
#
# python /usr/bin/virtualenv /path/to/desired/location
#
# The path to virtualenv may vary.
#
# @author: E.S. Rosenberg (Keeper of the Keys) <esr at mail dot hebrew dot edu>
# @license: GPLv2
###############################################################################

exit_codes = dict()
exit_codes['ok'] = 0
exit_codes['warning'] = 1
exit_codes['critical'] = 2
exit_codes['unknown'] = 3
exit_code = exit_codes['unknown']

string_results = []
string_perfdata = []

def set_exit(status):
    global exit_code
    if exit_code == exit_codes['unknown']:
        if status < exit_code:
            exit_code = status
    else:
        if status > exit_code:
            exit_code = status

def table_grep(table, search_string):
    global exit_code, exit_codes
    for entry in table:
        for mibO,value in entry:
            if value == search_string:
                print 'OK - string: ' + search_string + ' found at: ' + str(mibO)
                set_exit(exit_codes['ok'])
                exit(exit_code)
    print 'Critical - string: ' + search_string + ' not found!'
    set_exit(exit_codes['critical'])
    exit(exit_code) 
                

### Imports ###
try:
    import os
    # Python egg cash definition needed on systems where the running user lacks
    # write permission to the running dir.
    os.environ['PYTHON_EGG_CACHE'] = "/var/spool/nagios/python-eggs/"
    import argparse
    from snmp import *
except Exception as e:
    print "UNKNOWN: " + str(e)
    set_exit(exit_codes['unknown'])
    exit(exit_code)

### End Imports ###

if __name__ == "__main__":
    parser = argparse.ArgumentParser(__file__)

    parser.add_argument('-H', '--host', help = 'Hostname or IP address, if no ' +
                        'other arguments are specified all available info ' +
                        'will be printed', dest = 'snmp_host', required = True)
    parser.add_argument('-p', '--port', dest = 'snmp_port', default = 161,
                        help = 'SNMP Port, default 161')
    parser.add_argument('-C', help='SNMP community read string', 
                        default='public', dest='snmp_comm')
    parser.add_argument('-v', dest = 'snmp_vers', default = '2c',
                        help = 'SNMP version')
    parser.add_argument('-s', '--string',  help = 'Process name or string that '+
                        'needs to be present in the queried SNMP table.',
                        dest = 'search_string', required = True)
    parser.add_argument('-O', '--table-oid', dest = 'oids', nargs = '+',
                        help = 'List of OIDs of different tables to be searched.',
                        required = True)
    args = parser.parse_args()

    try:
        res = snmpWalk(args.snmp_host, args.snmp_port, 
                       snmpCreateAuthData(args.snmp_vers, args.snmp_comm), 
                       *args.oids)
    except Exception as e:
        print "UNKNOWN: " + str(e)
        set_exit(exit_codes['unknown'])
        exit(exit_code)

    table_grep(res, args.search_string)
