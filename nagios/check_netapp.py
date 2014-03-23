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
    import nagios
except Exception as e:
    print "UNKNOWN: " + str(e)
    exit(3)

oid_cpu = '1.3.6.1.4.1.789.1.2.1.3.0'
oid_nfsops = '1.3.6.1.4.1.789.1.2.2.1.0'
oid_uptime = '1.3.6.1.2.1.1.3.0'
oid_failed_fan = '1.3.6.1.4.1.789.1.2.4.2.0'
oid_failed_psu = '1.3.6.1.4.1.789.1.2.4.4.0'

snmp_host = ''
snmp_port = 161
snmp_comm = 'public'
snmp_vers = 1

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
        nagios.set_exit(nagios.exit_codes['unknown'])
        print e
        return

    thresholdCheck(result[0][1])
        
    nagios.string_results += ['CPU usage on {}: {}'.format(snmp_host, result[0][1])]
    perfdata = {'cur': result[0][1], 'w': xstr(args.warn), 'c': xstr(args.crit)}
    nagios.string_perfdata += ['cpu={cur};{w};{c};0;100'.format(**perfdata)]

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
        nagios.set_exit(nagios.exit_codes['unknown'])
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
    
    nagios.string_results += ['NfsOps/Sec on {} is: {}'.format(snmp_host, nfsops)]
    perfdata = {'val': nfsops, 'w': xstr(args.warn), 'c': xstr(args.crit), 
                'min': 0, 'max': '' }
    nagios.string_perfdata += ['nfsops/sec={val};{w};{c};{min};{max}'.format(
        **perfdata)]

def fanCheck():
    try:
        result = snmpGetter(oid_failed_fan)
    except Exception as e:
        nagios.set_exit(nagios.exit_codes['unknown'])
        print e
        return

    nagios.string_results += ['Failed Fans: {}'.format(result[0][1])]
    if result[0][1] > 0:
        nagios.set_exit(nagios.exit_codes['critical'])
    else:
        nagios.set_exit(nagios.exit_codes['ok'])

def psuCheck():
    try:
        result = snmpGetter(oid_failed_psu)
    except Exception as e:
        nagios.set_exit(nagios.exit_codes['unknown'])
        print e
        return

    nagios.string_results += ['Failed PSUs: {}'.format(result[0][1])]
    if result[0][1] > 0:
        nagios.set_exit(nagios.exit_codes['critical'])
    else:
        nagios.set_exit(nagios.exit_codes['ok'])

def thresholdCheck(var):
    """Check whether provided value is within threshold

    Currently this function only check that the value doesn't exceed a 
    threshold, to be truely handling thresholds the way nagios likes it it
    should be checking being inside a range.
    """
    global args
    if args.crit != None and var >= args.crit:
        nagios.set_exit(nagios.exit_codes['critical'])
    elif args.warn != None and var >= args.warn and exit_status != exit_critical:
        nagios.set_exit(nagios.exit_codes['warning'])
    else:
        nagios.set_exit(nagios.exit_codes['ok'])

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

    nagios.output_and_exit()
