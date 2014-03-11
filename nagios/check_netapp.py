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
# Based on work by David Peer 2006
# Written by E.S. Rosenberg 5773/2013
#
# Check NetApp systems stat via snmp v1/2 , written for Nagios
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

# The following two lines are a workaround for a local issue, you may very well
# not have it and not need them.
try:
    import os
    os.environ['PYTHON_EGG_CACHE'] = "/var/spool/nagios/python-eggs/"
    from pysnmp.entity.rfc3413.oneliner import cmdgen
    import time
    import argparse
except Exception as e:
    print "UNKNOWN: " + str(e)
    exit(3)

exit_ok = 0
exit_warning = 1
exit_critical = 2
exit_unknown = 3
exit_status = exit_unknown

oid_cpu = '1.3.6.1.4.1.789.1.2.1.3.0'
oid_nfsops = '1.3.6.1.4.1.789.1.2.2.1.0'
oid_uptime = '1.3.6.1.2.1.1.3.0'
oid_failed_fan = '1.3.6.1.4.1.789.1.2.4.2.0'
oid_failed_psu = '1.3.6.1.4.1.789.1.2.4.4.0'

snmp_host = ''
snmp_port = 161
snmp_comm = 'public'
snmp_vers = 1

string_result = []
string_performance_data = []

# TODO: move script to use snmp library.
def snmpGetter(*oids):

    global snmp_host, snmp_comm, snmp_port, snmp_vers
    cmdGen = cmdgen.CommandGenerator()
    snmpModel = 0

    if snmp_vers == 1:
        snmpModel = 0
    elif snmp_vers == '2c':
        snmpModel = 1

    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
        cmdgen.CommunityData(snmp_comm, mpModel = snmpModel),
        cmdgen.UdpTransportTarget((snmp_host, snmp_port)),
        *oids,
        lookupNames = True,
        lookupValues = True)

    if errorIndication:
        raise Exception("An Error Occurred: {}".format(errorIndication))
    else:
        if errorStatus:
            raise Exception('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex)-1] or '?')
            )
        else:
            return varBinds
    
    return false

def cpuCheck():
    try:
        result = snmpGetter(oid_cpu)
    except Exception as e:
        exit_status = exit_unknown
        print e
        return

    thresholdCheck(result[0][1])
    
    global string_result, string_performance_data
    
    string_result += ['CPU usage on {}: {}'.format(snmp_host, result[0][1])]
    perfdata = {'cur': result[0][1], 'w': xstr(args.warn), 'c': xstr(args.crit)}
    string_performance_data += ['cpu={cur};{w};{c};0;100'.format(**perfdata)]

def nfsiopsCheck():
    '''Check NFS IOops/second

    Function reads 2 samples about one second apart of iocount + timestamp and 
    calculates NFS IOops/second
    '''
    oids = [
        oid_uptime,
        oid_nfsops
    ]
    samples = []
    try:
        samples.append(snmpGetter(*oids))
        time.sleep(1)
        samples.append(snmpGetter(*oids))
    except Exception as e:
        exit_status = exit_unknown
        print e
        return        

    nfsops = []
    timestamps = []

    for sample in samples:
        for name, val in sample:
            if str(name) == oid_nfsops:
                nfsops.append(val)
            else:
                timestamps.append(val)
        
    nfsops = ((nfsops[1] - nfsops[0]) / 
               (int(timestamps[1] - timestamps[0]) / 100))

    thresholdCheck(nfsops)
    
    global string_result, string_performance_data
    string_result += ['NfsOps/Sec on {} is: {}'.format(snmp_host, nfsops)]
    perfdata = {'val': nfsops, 'w': xstr(args.warn), 'c': xstr(args.crit), 
                'min': 0, 'max': '' }
    string_performance_data += ['nfsops/sec={val};{w};{c};{min};{max}'.format(
        **perfdata)]

def fanCheck():
    global exit_warning, exit_critical, exit_status, exit_ok
    try:
        result = snmpGetter(oid_failed_fan)
    except Exception as e:
        exit_status = exit_unknown
        print e
        return

    global string_result
    string_result += ['Failed Fans: {}'.format(result[0][1])]
    if result[0][1] > 0:
        exit_status = exit_critical
    elif exit_status == exit_unknown:
        exit_status = exit_ok

def psuCheck():
    global exit_warning, exit_critical, exit_status, exit_ok
    try:
        result = snmpGetter(oid_failed_psu)
    except Exception as e:
        exit_status = exit_unknown
        print e
        return

    global string_result
    string_result += ['Failed PSUs: {}'.format(result[0][1])]
    if result[0][1] > 0:
        exit_status = exit_critical
    elif exit_status == exit_unknown:
        exit_status = exit_ok

def thresholdCheck(var):
    """Check whether prvided value is within threshold

    Currently this function only check that the value doesn't exceed a 
    threshold, to be truely handling thresholds the way nagios likes it it
    should be checking being inside a range.
    """
    global args, exit_warning, exit_critical, exit_status, exit_ok
    if args.crit != None and var >= args.crit:
        exit_status = exit_critical
    elif args.warn != None and var >= args.warn and exit_status != exit_critical:
        exit_status = exit_warning
    else:
        exit_status = exit_ok

def xstr(s):
    if s is None:
        return ''
    return str(s)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(__file__)
    
    parser.add_argument('-H', '--host', help='Hostname or IP address, if no ' +
                        'other arguments are specified all available info ' +
                        'will be printed', dest = 'snmp_host', required = True)
    parser.add_argument('-p', '--port', dest = 'snmp_port', default = 161,
                        help = 'SNMP Port, default 161')
    parser.add_argument('-C', help='SNMP community read string', 
                        default='public', dest='snmp_comm')
    parser.add_argument('-v', dest = 'snmp_vers', default = 1,
                        help = 'SNMP version')
    parser.add_argument('-cpu', action='store_true', dest='cpu',
                        help='Return CPU utilization')
    parser.add_argument('-nfso', action='store_true', dest='nfso',
                        help='Return NfsOps/sec estimate')
    parser.add_argument('-w', '--warn', type = int, default = None,
                         help='For Nagios determine warn threshold')
    parser.add_argument('-c', '--crit', type = int, default = None,
                        help='For Nagios determine critical threshold')

    args = parser.parse_args()

    snmp_host = args.snmp_host
    snmp_comm = args.snmp_comm
    snmp_vers = args.snmp_vers
    snmp_port = args.snmp_port

    if args.cpu == True:
        cpuCheck()
    if args.nfso == True:
        nfsiopsCheck()

    fanCheck()
    psuCheck()

    if exit_status == exit_critical:
        print "CRITICAL - " + string_result[0]
    elif exit_status == exit_warning:
        print "WARNING - " + string_result[0]
    elif exit_status == exit_ok:
        print "OK - " + string_result[0]
    else:
        print "UNKNOWN"

    for result in string_result[1:-1]:
        print result
    if len(string_performance_data) > 0:
        print string_result[-1] + "|"

        for perfdata in string_performance_data:
            print perfdata

    else:
        print string_result[-1]

    exit(exit_status)
