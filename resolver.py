#!/usr/bin/env python3

import argparse
import sys
import socket
import random
from struct import pack
from struct import unpack


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

    Returns (touple):
        string: The human readable string.
        int: position in the response where string ends

    Example:  networkToString('(3)www(8)sandiego(3)edu(0)', 0) will return
              ('www.sandiego.edu', 12)
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
            for i in range(6):
                offset += (length & 1 << i)
            for i in range(8):
                offset += (b2 & 1 << i)
            dereferenced = networkToString(response, offset)[0]
            return toReturn + dereferenced, position + 2

        formatString = str(length) + "s"
        position += 1
        toReturn += unpack(
                formatString, response[position:position+length])[0].decode()
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
    flags = 0   # 0 implies basic iterative query

    # one question, no answers for basic query
    num_questions = 1
    num_answers = 0
    num_auth = 0
    num_other = 0

    # "!HHHHHH" means pack 6 Half integers (i.e. 16-bit values) into a single
    # string, with data placed in network order (!)
    header = pack(
            "!HHHHHH", ID, flags, num_questions,
            num_answers, num_auth, num_other)

    qname = stringToNetwork(hostname)
    # request A type
    qtype = 1
    remainder = pack("!HH", qtype, 1)
    query = header + qname + remainder
    return query


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-m", "--mxlookup",  help="MX lookup", action="store_true")
    parser.add_argument("host_ip", help="Host name's IP address", type=str)
    args = parser.parse_args()
    return args

def getBits(bytes):
    for b in range(sys.getsizeof(bytes)):
        for i in range(8):
            yield(b >> i) & 1


def unpackResponse(response):
    '''
    id      2 bytes
    flags   2 bytes
    #q's    2 bytes
    #ansers 2 bytes
    auth rr 2 byres
    addit rr    2 bytes
    Question 'hame' starts at 12
        + 2 bytes for tye
        + 2 bytes for class
    Answers start right after last 2 of question:
        2 bytes for names response
        2 bytes for type
        2 bytes for class
        4 bytes for ttl
        2 bytes for length
        address of length specified starts at end of last query + 12
    '''
    id = unpack('!H', response[0:2])[0]
    flags = unpack('!H', response[2:4])[0]
    qdCount = unpack('!H', response[4:6])[0]
    anCount = unpack('!H', response[6:8])[0]
    nsCount = unpack('!H', response[8:10])[0]
    arCount = unpack('!H', response[10:12])[0]
    print("q:", qdCount, anCount, nsCount, arCount)

    # print(response[12])
    question = networkToString(response, 12)

    if nsCount == 0:
        return None
    # create list of tuples with servername and end index
    server_tuples = [networkToString(response, question[1] + 16)]
    for i in range(nsCount - 1):
        server_tuples.append(
                networkToString(response, server_tuples[i][1] + 12))

    # create list of first element of the tuple
    servers = [x[0] for x in server_tuples]
    #  for server in servers:
    #      print(server)
    return servers


def sendAndReceive(sock, port, query, servers):
    for ip_addr in servers:
        print(ip_addr)
        try:
            sock.sendto(query, (ip_addr, 53))
            response = sock.recv(4096)
            # You'll need to unpack any response you get using the unpack

            new_servers = unpackResponse(response)
            for s in new_servers:
                print(s)
            # know format of DNS messageis to know where to find the network

        except socket.timeout as e:
            print("Exception:", e)
        break
    #  sendAndReceive(sock, port, query, new_servers)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    args = parseArgs()

    with open('root-servers.txt') as f:
        servers = f.read().splitlines()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)   # socket should timeout after 5 seconds

    # create a query with a random id for hostname www.sandiego.edu's IP addr
    id = random.randint(0, 65535)
    print('id = ' + str(id))
    # this is an example
    # query = constructQuery(24021, "www.sandiego.edu")
    query = constructQuery(id, args.host_ip)

    sendAndReceive(sock, 53, query, servers)


if __name__ == "__main__":
    sys.exit(main())
