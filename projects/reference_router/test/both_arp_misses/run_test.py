#!/bin/env python

from NFTestLib import *
from PacketLib import *

import random

import sys
import os
sys.path.append(os.environ['NF_DESIGN_DIR']+'/lib/Python')
project = os.path.basename(os.environ['NF_DESIGN_DIR'])
reg_defines = __import__('reg_defines_'+project)

from RegressRouterLib import *

import scapy.all as scapy

interfaces = ("nf2c0", "nf2c1", "nf2c2", "nf2c3", "eth1", "eth2")

nftest_init(interfaces, 'conn')
nftest_start()

nftest_barrier()

routerMAC0 = "00:ca:fe:00:00:01"
routerMAC1 = "00:ca:fe:00:00:02"
routerMAC2 = "00:ca:fe:00:00:03"
routerMAC3 = "00:ca:fe:00:00:04"

routerIP0 = "192.168.0.40"
routerIP1 = "192.168.1.40"
routerIP2 = "192.168.2.40"
routerIP3 = "192.168.3.40"

# Write the mac and IP addresses
nftest_add_dst_ip_filter_entry ('nf2c0', 0, routerIP0)
nftest_add_dst_ip_filter_entry ('nf2c1', 1, routerIP1)
nftest_add_dst_ip_filter_entry ('nf2c2', 2, routerIP2)
nftest_add_dst_ip_filter_entry ('nf2c3', 3, routerIP3)

nftest_set_router_MAC ('nf2c0', routerMAC0)
nftest_set_router_MAC ('nf2c1', routerMAC1)
nftest_set_router_MAC ('nf2c2', routerMAC2)
nftest_set_router_MAC ('nf2c3', routerMAC3)

for i in range(32):
    nftest_invalidate_LPM_table_entry('nf2c0', i)

for i in range(32):
    nftest_invalidate_ARP_table_entry('nf2c0', i)

nftest_regwrite(reg_defines.ROUTER_OP_LUT_ARP_NUM_MISSES_REG(), 0)

index = 0
subnetIP = "192.168.1.0"
subnetMask = "255.255.255.0"
nextHopIP = "192.168.1.54"
outPort = 0x4
nextHopMAC = "dd:55:dd:66:dd:77"

nftest_add_LPM_table_entry('nf2c0', index, subnetIP, subnetMask, nextHopIP, outPort)

nftest_regwrite(reg_defines.ROUTER_OP_LUT_ARP_NUM_MISSES_REG(), 0)

nftest_barrier()

total_errors = 0

portPkts = scapy.rdpcap('eth1_pkts.pcap')

print "Sending packets"

for i in range(30):
    sent_pkt = portPkts[i]
    nftest_send('eth1', sent_pkt)
    nftest_expect('nf2c0', sent_pkt)

temp_error_val = 0

nftest_barrier()

temp_error_val = nftest_regread_expect(reg_defines.ROUTER_OP_LUT_ARP_NUM_MISSES_REG(), 30)
if isHW():
    if temp_error_val != 30:
        print "Expected 30 ARP misses.  Received " + str(temp_error_val)
        total_errors += 1

nftest_barrier()

total_errors += nftest_finish()

if total_errors == 0:
    print 'SUCCESS!'
    sys.exit(0)
else:
    print 'FAIL: ' + str(total_errors) + ' errors'
    sys.exit(1)
