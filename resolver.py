#!/usr/bin/env python3

import argparse
import sys
import socket
from struct import *

def stringToNetwork(orig_string):
    """
    Converts a standard string to a string that can be sent over
    the network.

    Args:
        orig_string (string): the string to convert

    Returns:
        bytes: The network formatted string (as bytes)

    Example:
        stringToNetwork('www.sandiego.edu.edu') will return
          (3)www(8)sandiego(3)edu(0)
    """
    ls = orig_string.split('.')
    toReturn = b""
    for item in ls:
        formatString = "B"
        formatString += str(len(item))
        formatString += "s"
        toReturn += pack(formatString, len(item), item.encode())
    toReturn += pack("B", 0)
    return toReturn


def networkToString(response, start):
    """
    Converts a network response string into a human readable string.

    Args:
        response (string): the entire network response message
        start (int): the location within the message where the network string
            starts.

    Returns:
        string: The human readable string.

    Example:  networkToString('(3)www(8)sandiego(3)edu(0)', 0) will return
              'www.sandiego.edu'
    """

    toReturn = ""
    position = start
    length = -1
    while True:
        length = unpack("!B", response[position:position+1])[0]
        if length == 0:
            position += 1
            break

        # Handle DNS pointers (!!)
        elif (length & 1 << 7) and (length & 1 << 6):
            b2 = unpack("!B", response[position+1:position+2])[0]
            offset = 0
            for i in range(6) :
                offset += (length & 1 << i)
            for i in range(8):
                offset += (b2 & 1 << i)
            dereferenced = networkToString(response, offset)[0]
            return toReturn + dereferenced, position + 2

        formatString = str(length) + "s"
        position += 1
        toReturn += unpack(formatString, response[position:position+length])[0].decode()
        toReturn += "."
        position += length
    return toReturn[:-1], position
    

def constructQuery(ID, hostname):
    """
    Constructs a DNS query message for a given hostname and ID.

    Args:
        ID (int): ID # for the message
        hostname (string): What we're asking for

    Returns: 
        string: "Packed" string containing a valid DNS query message
    """
    flags = 0 # 0 implies basic iterative query

    # one question, no answers for basic query
    num_questions = 1
    num_answers = 0
    num_auth = 0
    num_other = 0

    # "!HHHHHH" means pack 6 Half integers (i.e. 16-bit values) into a single
    # string, with data placed in network order (!)
    header = pack("!HHHHHH", ID, flags, num_questions, num_answers, num_auth,
            num_other)

    qname = stringToNetwork(hostname)
    qtype = 1 # request A type
    remainder = pack("!HH", qtype, 1)
    query = header + qname + remainder
    return query


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mxlookup",  help="MX lookup", action="store_true")
    parser.add_argument("host_ip", help="Host name's IP address", type=str)
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)   # socket should timeout after 5 seconds

    # create a query with a random id for hostname www.sandiego.edu's IP addr
    query = constructQuery(24021, "www.sandiego.edu")

    try:
        # send the message to 172.16.7.15 (the IP of USD's DNS server)
        sock.sendto(query, ("172.16.7.15", 53))
        response = sock.recv(4096)
        # You'll need to unpack any response you get using the unpack function

    except socket.timeout as e:
        print("Exception:", e)

if __name__ == "__main__":
    sys.exit(main())
