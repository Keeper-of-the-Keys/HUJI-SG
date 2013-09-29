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
# 

# The following two lines are a workaround for a local issue, you may very well
# not have it and not need them.
import os
os.environ['PYTHON_EGG_CACHE'] = "/var/spool/nagios/python-eggs/"

from snmp import *
import argparse

exit_codes = dict()
exit_codes['ok'] = 0
exit_codes['warning'] = 1
exit_codes['critical'] = 2
exit_codes['unknown'] = 3
exit_code = exit_codes['unknown']

string_results = []
string_perfdata = []

def check_temp(snmp_host, snmp_port, auth_data):
    global exit_codes, string_results, string_perfdata
    oid_vendor = '1.3.6.1.4.1.2769'
    oids = []

    oid_temp_rear = oid_vendor + '.2.1.1.1.3.0'
    oids.append(oid_temp_rear)
    
    oid_temp_water_in = oid_vendor + '.2.1.1.9.2.0'
    oids.append(oid_temp_water_in)

    oid_temp_water_in_warn = oid_vendor + '.2.1.1.9.3.0'
    oids.append(oid_temp_water_in_warn)

    oid_temp_water_in_crit = oid_vendor + '.2.1.1.9.4.0'
    oids.append(oid_temp_water_in_crit)

    results = dict(snmpGetter(snmp_host, snmp_port, auth_data, *oids))

    for (key, value) in results.iteritems():
        results[str(key)] = results.pop(key)

    if results[oid_temp_water_in] >= results[oid_temp_water_in_crit]:
        set_exit(exit_codes['critical'])
    elif results[oid_temp_water_in]  >= results[oid_temp_water_in_warn]:
        set_exit(exit_codes['warning'])
    else:
        set_exit(exit_codes['ok'])

    string_results += ["water_in = {}, warn = {}, crit = {}".format(
        float(results[oid_temp_water_in])/10, 
        float(results[oid_temp_water_in_warn])/10,
        float(results[oid_temp_water_in_crit])/10
    )]

    string_perfdata += ['water_in={};{};{};0;30'.format(
        float(results[oid_temp_water_in])/10, 
        float(results[oid_temp_water_in_warn])/10,
        float(results[oid_temp_water_in_crit])/10
    )]
 
def set_exit(status):
    global exit_code
    if status < exit_code:
        exit_code = status

def output_and_exit():
    global exit_code, exit_codes, string_results, string_perfdata

    if len(string_results) == 1 and len(string_perfdata) > 0:
        pipe_char = '|'
    else:
        pipe_char = ''

    if exit_code == exit_codes['critical']:
        print "CRITICAL - " + string_results[0] + pipe_char
    elif exit_code == exit_codes['warning']:
        print "WARNING - " + string_results[0] + pipe_char
    elif exit_code == exit_codes['ok']:
        print "OK - " + string_results[0] + pipe_char
    else:
        print "UNKNOWN"

    for result in string_results[1:-1]:
        print result
    
    if len(string_perfdata) > 0:
        if len(string_results) > 1:
            print string_results[-1] + "|"

        for perfdata in string_perfdata:
            print perfdata
    elif len(string_results) > 1:
        print string_results[-1]

    exit(exit_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__file__)

    parser.add_argument('-H', '--host', help='Hostname or IP address, if no ' +
                        'other arguments are specified all available info ' +
                        'will be printed', dest = 'snmp_host', required = True)
    parser.add_argument('-p', '--port', dest = 'snmp_port', default = 161,
                        help = 'SNMP Port, default 161')
    parser.add_argument('-C', help='SNMP community read string', 
                        default='public', dest='snmp_comm')
    parser.add_argument('-v', dest = 'snmp_vers', default = '2c',
                        help = 'SNMP version')

    args = parser.parse_args()

    try:
        check_temp(args.snmp_host, args.snmp_port, 
                   snmpCreateAuthData(args.snmp_vers, args.snmp_comm))
    except Exception as e:
        print "UNKNOWN" + str(e)
        set_exit(exit_codes['unknown'])
        exit(exit_code)

    output_and_exit()
