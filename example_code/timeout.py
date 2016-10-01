#!/usr/bin/env python

'''
Example code showing how to set the timeout time of a socket.
'''

import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)

print 'Calling recvfrom()'

try:
    result = sock.recvfrom(8192)
    print result
except socket.timeout as e:
    print 'Exception:', e
