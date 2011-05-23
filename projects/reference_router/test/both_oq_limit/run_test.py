#!/bin/env python

from NFTestLib import *
from PacketLib import *

from RegressRouterLib import *

import random

import sys
import os
sys.path.append(os.environ['NF_DESIGN_DIR']+'/lib/Python')
project = os.path.basename(os.environ['NF_DESIGN_DIR'])
reg_defines = __import__('reg_defines_'+project)

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

dstIP0 = "192.168.0.50"
dstIP1 = "192.168.1.50"
dstIP2 = "192.168.2.50"
dstIP3 = "192.168.3.50"

dstMAC0 = "aa:bb:cc:dd:ee:01"
dstMAC1 = "aa:bb:cc:dd:ee:02"
dstMAC2 = "aa:bb:cc:dd:ee:03"
dstMAC3 = "aa:bb:cc:dd:ee:04"

ALLSPFRouters = "224.0.0.5"

# clear LPM table
for i in range(32):
    nftest_invalidate_LPM_table_entry('nf2c0', i)

# clear ARP table
for i in range(32):
    nftest_invalidate_ARP_table_entry('nf2c0', i)

# Write the mac and IP addresses
nftest_add_dst_ip_filter_entry ('nf2c0', 0, routerIP0)
nftest_add_dst_ip_filter_entry ('nf2c1', 1, routerIP1)
nftest_add_dst_ip_filter_entry ('nf2c2', 2, routerIP2)
nftest_add_dst_ip_filter_entry ('nf2c3', 3, routerIP3)
nftest_add_dst_ip_filter_entry ('nf2c0', 4, ALLSPFRouters)

nftest_set_router_MAC ('nf2c0', routerMAC0)
nftest_set_router_MAC ('nf2c1', routerMAC1)
nftest_set_router_MAC ('nf2c2', routerMAC2)
nftest_set_router_MAC ('nf2c3', routerMAC3)

if isHW():
    nftest_regread_expect(reg_defines.MDIO_PHY_0_CONTROL_REG(), 0x1140)
    nftest_regread_expect(reg_defines.MDIO_PHY_1_CONTROL_REG(), 0x1140)
    nftest_regread_expect(reg_defines.MDIO_PHY_2_CONTROL_REG(), 0x5140)
    nftest_regread_expect(reg_defines.MDIO_PHY_3_CONTROL_REG(), 0x5140)

NUM_PKTS = 5

DA = routerMAC0
SA = "aa:bb:cc:dd:ee:ff"
TTL = 64
DST_IP = "192.168.1.1"
SRC_IP = "192.168.0.1"
nextHopMAC = "dd:55:dd:66:dd:77"

hdr = scapy.Ether(dst=DA, src=SA, type=0x800)/scapy.IP(dst=DST_IP, src=SRC_IP, ttl=TTL)

precreated0 = scapy.rdpcap('precreated0.pcap')
precreated1 = scapy.rdpcap('precreated1.pcap')
precreated2 = scapy.rdpcap('precreated2.pcap')
precreated3 = scapy.rdpcap('precreated3.pcap')

nftest_regwrite(reg_defines.OQ_QUEUE_0_NUM_PKTS_DROPPED_REG(), 0)
nftest_regwrite(reg_defines.OQ_QUEUE_2_NUM_PKTS_DROPPED_REG(), 0)
nftest_regwrite(reg_defines.OQ_QUEUE_4_NUM_PKTS_DROPPED_REG(), 0)
nftest_regwrite(reg_defines.OQ_QUEUE_6_NUM_PKTS_DROPPED_REG(), 0)

nftest_barrier()

for i in range(NUM_PKTS):
    pkt = precreated0[i]
    nftest_send('nf2c0', pkt)
    nftest_expect('eth1', pkt)

    pkt = precreated1[i]
    nftest_send('nf2c1', pkt)
    nftest_expect('eth2', pkt)

    pkt = precreated2[i]
    nftest_send('nf2c2', pkt)
    nftest_expect('nf2c2', pkt)

    pkt = precreated3[i]
    nftest_send('nf2c3', pkt)
    nftest_expect('nf2c3', pkt)


nftest_barrier()

print "Disabling servicing output queues"
nftest_regwrite(reg_defines.OQ_QUEUE_0_CTRL_REG(), 0)
nftest_regwrite(reg_defines.OQ_QUEUE_2_CTRL_REG(), 0)
nftest_regwrite(reg_defines.OQ_QUEUE_4_CTRL_REG(), 0)
nftest_regwrite(reg_defines.OQ_QUEUE_6_CTRL_REG(), 0)

print "Setting max number of pkts in queue to " + str(NUM_PKTS)
nftest_regwrite(reg_defines.OQ_QUEUE_0_MAX_PKTS_IN_Q_REG(), NUM_PKTS)
nftest_regwrite(reg_defines.OQ_QUEUE_2_MAX_PKTS_IN_Q_REG(), NUM_PKTS)
nftest_regwrite(reg_defines.OQ_QUEUE_4_MAX_PKTS_IN_Q_REG(), NUM_PKTS)
nftest_regwrite(reg_defines.OQ_QUEUE_6_MAX_PKTS_IN_Q_REG(), NUM_PKTS)

print "Resending packets."
nftest_barrier()
sent = [[],[],[],[]]
for i in range(NUM_PKTS):
    pkt = precreated0[i]
    nftest_send('nf2c0', pkt); sent[0].append(pkt)

    pkt = precreated1[i]
    nftest_send('nf2c1', pkt); sent[1].append(pkt)

    pkt = precreated2[i]
    nftest_send('nf2c2', pkt); sent[2].append(pkt)

    pkt = precreated3[i]
    nftest_send('nf2c3', pkt); sent[3].append(pkt)

nftest_barrier()

print "\nVerifying that the packets are stored in the output queues"
nftest_regread_expect(reg_defines.OQ_QUEUE_0_NUM_PKTS_IN_Q_REG(), NUM_PKTS)
nftest_regread_expect(reg_defines.OQ_QUEUE_2_NUM_PKTS_IN_Q_REG(), NUM_PKTS)
nftest_regread_expect(reg_defines.OQ_QUEUE_4_NUM_PKTS_IN_Q_REG(), NUM_PKTS)
nftest_regread_expect(reg_defines.OQ_QUEUE_6_NUM_PKTS_IN_Q_REG(), NUM_PKTS)

print "Sending more packets that should be dropped."
nftest_barrier()
for i in range(NUM_PKTS):
    pkt = precreated0[i]
    nftest_send('nf2c0', pkt)

    pkt = precreated1[i]
    nftest_send('nf2c1', pkt)

    pkt = precreated2[i]
    nftest_send('nf2c2', pkt)

    pkt = precreated3[i]
    nftest_send('nf2c3', pkt)

nftest_barrier()

for i in range(4):
    for pkt in sent[i]:
        if i > 1:
            nftest_expect('nf2c'+str(i), pkt)
        else:
            nftest_expect('eth'+str(i+1), pkt)

print "Verifying dropped pkts counter."
nftest_regread_expect(reg_defines.OQ_QUEUE_0_NUM_PKTS_DROPPED_REG(), NUM_PKTS)
nftest_regread_expect(reg_defines.OQ_QUEUE_2_NUM_PKTS_DROPPED_REG(), NUM_PKTS)
nftest_regread_expect(reg_defines.OQ_QUEUE_4_NUM_PKTS_DROPPED_REG(), NUM_PKTS)
nftest_regread_expect(reg_defines.OQ_QUEUE_6_NUM_PKTS_DROPPED_REG(), NUM_PKTS)

print "Start servicing the output queues again. Packets should be sent out."
nftest_regwrite(reg_defines.OQ_QUEUE_0_CTRL_REG(), 1 << reg_defines.OQ_ENABLE_SEND_BIT_NUM())
nftest_regwrite(reg_defines.OQ_QUEUE_2_CTRL_REG(), 1 << reg_defines.OQ_ENABLE_SEND_BIT_NUM())
nftest_regwrite(reg_defines.OQ_QUEUE_4_CTRL_REG(), 1 << reg_defines.OQ_ENABLE_SEND_BIT_NUM())
nftest_regwrite(reg_defines.OQ_QUEUE_6_CTRL_REG(), 1 << reg_defines.OQ_ENABLE_SEND_BIT_NUM())

print "Reset max number of pkts in queues."
nftest_regwrite(reg_defines.OQ_QUEUE_0_MAX_PKTS_IN_Q_REG(), 0xffffffff)
nftest_regwrite(reg_defines.OQ_QUEUE_2_MAX_PKTS_IN_Q_REG(), 0xffffffff)
nftest_regwrite(reg_defines.OQ_QUEUE_4_MAX_PKTS_IN_Q_REG(), 0xffffffff)
nftest_regwrite(reg_defines.OQ_QUEUE_6_MAX_PKTS_IN_Q_REG(), 0xffffffff)

nftest_barrier()

total_errors = nftest_finish()

if total_errors == 0:
    print 'SUCCESS!'
    sys.exit(0)
else:
    print 'FAIL: ' + str(total_errors) + ' errors'
    sys.exit(1)
