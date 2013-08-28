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

################################################################################
# This monitors the transactions per second (tps) handled by a postgreSQL server
#
# Based on code written by Danny Braniss <danny at cs dot huji dot ac dot il>
#
# Contains 2 functions:
#  tps(dbhost, inteval) - closest to original code, produces output for
#                         terminal/file logging in eternal loop.
#  tps_nagios(args) - version of function that produces output, exit statuses
#                     and perfdata for nagios
#
# @author: E.S. Rosenberg (Keeper of the Keys) <esr at mail dot hebrew dot edu>
# @license: GPLv2
################################################################################

from datetime import datetime
import sys
import signal
import argparse

from psycopg2 import connect, extensions, extras, errorcodes
import time

def tps(dbhost, interval):
    """Figure out Transactions per second for PostgreSQL and write to file
    """

    from time import sleep

    cmd = "SELECT extract ('epoch' FROM now()) as stamp, sum(xact_commit"
    cmd += " + xact_rollback) as total from pg_stat_database"

    max = 0
    last = dict(stamp = 0.0, total = 0)

    while True:
        # Connection is established and closed inside the loop to prevent other
        # users being locked out.
        con = connect(host = dbhost, database = 'template1')
        cur = con.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute(cmd)
        res = cur.fetchone()

        if last['stamp']:
            elapsed = res['stamp'] - last['stamp']
            trans = int(res['total']) - last['total']
            ts = datetime.fromtimestamp(res['stamp'])
            tps = int(trans/int(elapsed))
            if tps > max:
                max = tps
            print '{} {:10} {:10}'.format(ts.strftime('%d/%m %X'),
                                          tps, max)
            sys.stdout.flush()
        last = res
        con.close()
        sleep(interval)

def tps_nagios(dbhost, prev = '', warn = 0, crit = 0, db = 'template1'):
    """Figure out Transactions per second for PostgreSQL and return to nagios

    Takes:
    dbhost - hostname of host to check
    prev - takes $LONGSERVICEOUTPUT$
    warn - warning threshold, 0 = no warning level
    crit - critical threshold, 0 = no critical level
    db - db name to connect to

    Returns:
    A string that nagios can process and an appropriate exit state

    Nagios command_line definition should look something like this:
    command_line /path/to/check_pgsql_tps.py -m nagios
    --last '$LONGSERVICEOUTPUT$' $HOSTADDRESS$ $ARG1$
    """
    
    cmd = "SELECT extract ('epoch' FROM now()) as stamp, sum(xact_commit"
    cmd += " + xact_rollback) as total from pg_stat_database"

    con = connect(host = dbhost, database = db)
    cur = con.cursor(cursor_factory=extras.RealDictCursor)
    cur.execute(cmd)
    res = cur.fetchone()
    con.close()

    if(prev != '' and prev.find('exception') < 0):
        last = prev.rstrip('\\n').strip("\\").split(' ')

        elapsed = res['stamp'] - float(last[0])
        transactions = res['total'] - int(last[1])
        tps = int(transactions)/elapsed

        if(crit > 0 and tps > crit):
            print "CRITICAL - TPS: {tps} | TPS={tps}".format(tps=str(tps))
            ret = 2
        elif(warn > 0 and tps > warn):
            print "WARNING - TPS: {tps} | TPS={tps}".format(tps=str(tps))
            ret = 1
        else:
            print "OK - TPS: {tps} | TPS={tps}".format(tps=str(tps))
            ret = 0

    else:
        print "OK 0 Initial results"
        ret = 0

    print "{} {}".format(str(res['stamp']), str(res['total']))

    return ret

def debug(var):
    """Simple function to quickly print the value of any variable
    """
    import pprint
    pprint.pprint(var)

def ctrlc_handler(signal, frame):
    """Handler for ctrl+c/SIGINT/any signal to gracefully quit.
    """
    print "Goodbye"
    sys.exit(0)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(__file__)
    
    parser.add_argument('-m', '--mode', dest='mode', default='standalone',
                        choices=['nagios', 'standalone'])
    parser.add_argument('-w', '--warn', type=int,
                        help='For Nagios determine warn threshold')
    parser.add_argument('-c', '--crit', type=int,
                        help='For Nagios determine critical threshold')
    parser.add_argument('-l', '--last', default='',
                        help='Previous check result')
    parser.add_argument('-d', '--database', default='template1',
                        help='Database to connect to')
    parser.add_argument('host', nargs='?', default='moo-02')

    args = parser.parse_args()
    ret = 3

    signal.signal(signal.SIGINT, ctrlc_handler)

    if(args.mode == 'standalone'):
        tps(args.host, 10)
        ret = 0
    elif(args.mode == 'nagios'):
        try:
            ret = tps_nagios(args.host, prev = args.last, crit = args.crit, warn = args.warn, db = args.database)
        except:
            print "an exception happened ", sys.exc_info()
            ret = 3

    exit(ret)
