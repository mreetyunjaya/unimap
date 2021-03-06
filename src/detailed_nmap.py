#!/usr/bin/env python

import os
import socket
import subprocess
import multiprocessing
from multiprocessing import Process,Queue
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

from src.core import *

def scan_func(port, service, scripts, scandir, ipaddr):
    global NMAP_SCAN
    NMAP_SCAN = 'nmap -Pn -n --open -T4 -p {0} --script="{1}" -oN {2}/nmap_{3}.nmap {4}'.format(port, 
        scripts, scandir, service, ipaddr)
    return NMAP_SCAN


def id_services(scandir):
    print("\n{0}[>]{1} Checking for Detailed Nmap Scan Services".format(bcolors.BLUE, bcolors.ENDC))
    # Variables
    global service_dict
    global script_dict
    service_dict = {}
    script_dict = {
        'ssh': SSH_SCRIPTS, 
        'ftp': FTP_SCRIPTS, 
        'domain': DNS_SCRIPTS, 
        'http': HTTP_SCRIPTS,
        'microsoft-ds': WIN_SCRIPTS,
        'rpcbind': RPC_SCRIPTS,
        'ms-wbt-server': RDP_SCRIPTS,
        'snmp': SNMP_SCRIPTS,
        'ms-sql': MSSQL_SCRIPTS,
        'oracle': ORACLE_SCRIPTS,
        'mysql': MYSQL_SCRIPTS,
        'mongod': MONGODB_SCRIPTS,
        }
    
    # Generate basic mapping of ports to services
    with open('{0}/basic_nmap.nmap'.format(scandir), 'r') as f:
        basic_results = [line for line in f.readlines() if 'open' in line]
    for result in basic_results:
        ports = []
        if ('tcp' in result) and ('open' in result) and not ('Discovered' in result):
            service = result.split()[2]
            if service == 'ssl/http':
                service = 'https'
            else: pass
            port = result.split()[0]
            
            if service in service_dict:
                ports = service_dict[service]
                
            ports.append(port)
            service_dict[service] = ports
            
    if len(service_dict) > 0:
        print("{0}[+]{1} Running Detailed Nmap Scans on {2} Services\n".format(bcolors.GREEN, bcolors.ENDC, str(len(service_dict))))


def nmap_scan((port, scripts, scandir, service, ipaddr, quiet)):
    NMAP_SCAN = 'nmap -Pn -n --open -T4 -p {0} --script="{1}" -oN {2}/nmap_{0}.nmap {3}'.format(port,
            scripts, scandir, ipaddr)
    if quiet is not True:
        print("{0}[*]{1} Running Nmap Script Scans on {2}".format(bcolors.YELLOW, bcolors.ENDC, service))
    else: pass
    with open(os.devnull, 'w') as FNULL:
        try:
            subprocess.call(NMAP_SCAN, stdout=FNULL, shell=True)
            if quiet is not True:
                print("{0}[+]{1} Finished Nmap Script Scans on {2}".format(bcolors.GREEN, bcolors.ENDC, service))
            else: pass
        except subprocess.CalledProcessError as e:
            raise RuntimeError("command '{0}' return with error (code {1}): {2}".format(e.cmd, e.returncode, e.output))


def detailed_nmap(ipaddr, scandir, quiet):
    id_services(scandir)
    jobs = []
    for service in service_dict:
        for script in script_dict:
            if script in service:
                scripts = script_dict[script]
                for port in service_dict[service]:
                    port = port.split('/')[0]
                    jobs.append((port, scripts, scandir, service, ipaddr, quiet))

    pool = ThreadPool(4)
    pool.map(nmap_scan, jobs)
