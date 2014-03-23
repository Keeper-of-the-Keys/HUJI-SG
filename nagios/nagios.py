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
# Library with some basic nagios related stuff, that kept repeating itself.
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

def output_and_exit():
    global exit_code, exit_codes, string_results, string_perfdata

    if len(string_results) == 1 and len(string_perfdata) > 0:
        pipe_char = '\n|'
    else:
        pipe_char = ''

    if exit_code == exit_codes['critical']:
        output = "CRITICAL"
    elif exit_code == exit_codes['warning']:
        output = "WARNING"
    elif exit_code == exit_codes['ok']:
        output = "OK"
    else:
        output = "UNKNOWN"

    if len(string_results) >= 1:
        output += ": " + string_results[0] + pipe_char

    print output
 
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
