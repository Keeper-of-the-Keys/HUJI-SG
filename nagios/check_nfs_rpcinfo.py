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
# This script will try to ascertain whether all processes needed for NFS are 
# running on the NFS server, it uses rpcinfo which is called through the python
# subprocess module.
#
# It also depends on the HUJI nagios library
#
# @author: E.S. Rosenberg (Keeper of the Keys) <esr at mail dot hebrew dot edu>
# @license: GPLv2
###############################################################################

### Imports ###
try:
    import huji_cs_nagios
    import argparse
    from subprocess import check_output
except Exception as e:
    print "UNKNOWN: " + str(e)
    exit(3) # 3 is Nagios "unknown"

### End Imports ###

def check_procs(host):
    process_list = ["nfs", "mountd", "portmapper", "nlockmg"]

    rpcinfo_output = check_output(["rpcinfo", "-p", host])

    for process in process_list:
        if(rpcinfo_output.find(process) == -1):
            huji_cs_nagios.set_exit(huji_cs_nagios.exit_codes['critical'])
            huji_cs_nagios.string_results += ['process: {} not found in RPC'.format(
                process
            )]

    huji_cs_nagios.set_exit(huji_cs_nagios.exit_codes['ok'])
    if(huji_cs_nagios.exit_code == huji_cs_nagios.exit_codes['ok']):
        huji_cs_nagios.string_results += ['All processes required for NFS found']


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__file__)

    parser.add_argument('-H', '--host', help = 'Hostname or IP address, if no ' +
                        'other arguments are specified all available info ' +
                        'will be printed', dest = 'host', required = True)

    args = parser.parse_args()

    try:
        check_procs(args.host)
    except Exception as e:
        print "UNKNOWN: " + str(e)
        huji_cs_nagios.set_exit(huji_cs_nagios.exit_codes['unknown'])
        exit(huji_cs_nagios.exit_code)

    huji_cs_nagios.output_and_exit()
