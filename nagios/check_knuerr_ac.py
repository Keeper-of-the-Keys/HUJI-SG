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

### Imports ###
try:
    import nagios
except Exception as e:
    print "UNKNOWN: " + str(e)
    exit(3)

try:
    import os
    # Python egg cash definition needed on systems where the running user lacks
    # write permission to the running dir.
    os.environ['PYTHON_EGG_CACHE'] = "/var/spool/nagios/python-eggs/"
    import argparse
    from snmp import *
except Exception as e:
    print "UNKNOWN: " + str(e)
    nagios.set_exit(nagios.exit_codes['unknown'])
    exit(nagios.exit_code)

### End Imports ###

def verify_levels(level, warn, crit):
    if level >= crit:
        nagios.set_exit(nagios.exit_codes['critical'])
    elif level >= warn:
        nagios.set_exit(nagios.exit_codes['warning'])
    else:
        nagios.set_exit(nagios.exit_codes['ok'])

def check_temp(snmp_host, snmp_port, auth_data):
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

    nagios.string_results += ["water_in: {}, warn: {}, crit: {}".format(
        float(results[oid_temp_water_in])/10, 
        float(results[oid_temp_water_in_warn])/10,
        float(results[oid_temp_water_in_crit])/10
    )]

    nagios.string_perfdata += ['water_in={};{};{};0;30'.format(
        float(results[oid_temp_water_in])/10, 
        float(results[oid_temp_water_in_warn])/10,
        float(results[oid_temp_water_in_crit])/10
    )]

    nagios.string_results += ["water_out: {}, warn: {}, crit: {}".format(
        float(results[oid_temp_water_out])/10, 
        float(results[oid_temp_water_out_warn])/10,
        float(results[oid_temp_water_out_crit])/10
    )]

    nagios.string_perfdata += ['water_out={};{};{};0;30'.format(
        float(results[oid_temp_water_out])/10, 
        float(results[oid_temp_water_out_warn])/10,
        float(results[oid_temp_water_out_crit])/10
    )]

    nagios.string_results += ['humidity: {}%, warn: {}%, crit: {}%'.format(
        float(results[oid_humidity])/10,
        float(results[oid_humidity_warn])/10,
        float(results[oid_humidity_crit])/10
    )]

    nagios.string_perfdata += ['humidity={};{};{};0;100'.format(
        float(results[oid_humidity])/10,
        float(results[oid_humidity_warn])/10,
        float(results[oid_humidity_crit])/10
    )]

    nagios.string_perfdata += ['temp_front={};;;0;30'.format(
        float(results[oid_temp_front])/10
    )]

    nagios.string_perfdata += ['temp_rear={};;;0;30'.format(
        float(results[oid_temp_rear])/10
    )]
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(__file__)

    parser.add_argument('-H', '--host', help = 'Hostname or IP address, if no ' +
                        'other arguments are specified all available info ' +
                        'will be printed', dest = 'snmp_host', required = True)
    parser.add_argument('-p', '--port', dest = 'snmp_port', default = 161,
                        help = 'SNMP Port, default 161')
    parser.add_argument('-C', help = 'SNMP community read string', 
                        default = 'public', dest = 'snmp_comm')
    parser.add_argument('-v', dest = 'snmp_vers', default = '2c',
                        help = 'SNMP version')

    args = parser.parse_args()

    try:
        check_temp(args.snmp_host, args.snmp_port, 
                   snmpCreateAuthData(args.snmp_vers, args.snmp_comm))
    except Exception as e:
        print "UNKNOWN: " + str(e)
        nagios.set_exit(nagios.exit_codes['unknown'])
        exit(nagios.exit_code)

    nagios.output_and_exit()
