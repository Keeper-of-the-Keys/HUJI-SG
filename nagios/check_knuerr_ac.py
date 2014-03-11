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
# Written by E.S. Rosenberg 5774/2013 
#
# This script requieres PySNMP.
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

def verify_levels(level, warn, crit):
    if level >= crit:
        set_exit(exit_codes['critical'])
    elif level >= warn:
        set_exit(exit_codes['warning'])
    else:
        set_exit(exit_codes['ok'])

def check_temp(snmp_host, snmp_port, auth_data):
    global exit_codes, string_results, string_perfdata

    #### Setup OIDs ####
    # The following OIDs are according to KNUERR-COOLCON-MIB-V10.mib
    # Please make sure your products MIB is the same or modify this section.

    oid_vendor = '1.3.6.1.4.1.2769'
    oids = []

    oid_temp_rear = oid_vendor + '.2.1.1.1.3.0'
    oids.append(oid_temp_rear)

    oid_temp_front = oid_vendor + '.2.1.1.2.3.0'
    oids.append(oid_temp_front)
    
    oid_temp_water_in = oid_vendor + '.2.1.1.9.2.0'
    oids.append(oid_temp_water_in)

    oid_temp_water_in_warn = oid_vendor + '.2.1.1.9.3.0'
    oids.append(oid_temp_water_in_warn)

    oid_temp_water_in_crit = oid_vendor + '.2.1.1.9.4.0'
    oids.append(oid_temp_water_in_crit)

    oid_temp_water_out = oid_vendor + '.2.1.1.8.2.0'
    oids.append(oid_temp_water_out)

    oid_temp_water_out_warn = oid_vendor + '.2.1.1.8.3.0'
    oids.append(oid_temp_water_out_warn)

    oid_temp_water_out_crit = oid_vendor + '.2.1.1.8.4.0'
    oids.append(oid_temp_water_out_crit)

    oid_humidity = oid_vendor + '.2.1.1.7.2.0'
    oids.append(oid_humidity)

    oid_humidity_warn = oid_vendor + '.2.1.1.7.3.0'
    oids.append(oid_humidity_warn)

    oid_humidity_crit = oid_vendor + '.2.1.1.7.4.0'
    oids.append(oid_humidity_crit)
    #### End Setup OIDs ####

    results = dict(snmpGetter(snmp_host, snmp_port, auth_data, *oids))

    for (key, value) in results.iteritems():
        results[str(key)] = results.pop(key)

    verify_levels(results[oid_temp_water_in], results[oid_temp_water_in_warn],
                  results[oid_temp_water_in_crit])

    verify_levels(results[oid_temp_water_out], results[oid_temp_water_out_warn],
                  results[oid_temp_water_out_crit])

    verify_levels(results[oid_humidity], results[oid_humidity_warn],
                  results[oid_humidity_crit])

    string_results += ["water_in: {}, warn: {}, crit: {}".format(
        float(results[oid_temp_water_in])/10, 
        float(results[oid_temp_water_in_warn])/10,
        float(results[oid_temp_water_in_crit])/10
    )]

    string_perfdata += ['water_in={};{};{};0;30'.format(
        float(results[oid_temp_water_in])/10, 
        float(results[oid_temp_water_in_warn])/10,
        float(results[oid_temp_water_in_crit])/10
    )]

    string_results += ["water_out: {}, warn: {}, crit: {}".format(
        float(results[oid_temp_water_out])/10, 
        float(results[oid_temp_water_out_warn])/10,
        float(results[oid_temp_water_out_crit])/10
    )]

    string_perfdata += ['water_out={};{};{};0;30'.format(
        float(results[oid_temp_water_out])/10, 
        float(results[oid_temp_water_out_warn])/10,
        float(results[oid_temp_water_out_crit])/10
    )]

    string_results += ['humidity: {}%, warn: {}%, crit: {}%'.format(
        float(results[oid_humidity])/10,
        float(results[oid_humidity_warn])/10,
        float(results[oid_humidity_crit])/10
    )]

    string_perfdata += ['humidity={};{};{};0;100'.format(
        float(results[oid_humidity])/10,
        float(results[oid_humidity_warn])/10,
        float(results[oid_humidity_crit])/10
    )]

    string_perfdata += ['temp_front={};;;0;30'.format(
        float(results[oid_temp_front])/10
    )]

    string_perfdata += ['temp_rear={};;;0;30'.format(
        float(results[oid_temp_rear])/10
    )]
    

def output_and_exit():
    global exit_code, exit_codes, string_results, string_perfdata

    if len(string_results) == 1 and len(string_perfdata) > 0:
        pipe_char = '\n|'
    else:
        pipe_char = ''

    if exit_code == exit_codes['critical']:
        print "CRITICAL: " + string_results[0] + pipe_char
    elif exit_code == exit_codes['warning']:
        print "WARNING: " + string_results[0] + pipe_char
    elif exit_code == exit_codes['ok']:
        print "OK: " + string_results[0] + pipe_char
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
        print "UNKNOWN: " + str(e)
        set_exit(exit_codes['unknown'])
        exit(exit_code)

    output_and_exit()
