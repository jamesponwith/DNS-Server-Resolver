#!/usr/bin/env python3
"""
DNS Quesry Resolver
Project 03

Author 1: Patrick Hall
Author 2: James Ponwith


This program implements an elegent recursive solution
to an iterative problem. Conducts an iterative DNS 
query for a specified domain name mimicking nslookup
and dig. 

We should add a -d flag option for arugments to mimic
dig 

"""


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


def getServerIps(response, server_name_tuples, arCount):
    ''' 
    Gets the list of server ips
    '''
    server_ips = []
    len_index = server_name_tuples[-1][1] + 10
    for i in range(arCount):
        ip_addr_index = len_index + 2
        length = unpack('!H', response[len_index:len_index + 2])[0]
        if length == 4:
            server_ips.append(str(socket.inet_ntoa(
                response[ip_addr_index:ip_addr_index + 4])))
            len_index += 16
        if length == 16:
            len_index += 28 
    return server_ips


def getServerNames(response, nsCount):
    '''
    Gets the list of server names as tuples
    we know where the authority rrs start from here
    '''
    question = networkToString(response, 12)
    server_name_tuples = [networkToString(response, question[1] + 16)]
    for i in range(nsCount-1):
        server_name_tuples.append(
                networkToString(response, server_name_tuples[i][1] + 12))
    servers_name_list = [x[0] for x in server_name_tuples]
    return server_name_tuples



def unpackResponse(response):
    '''
    Unpacks the response for the list of server ips
    '''
    id = unpack('!H', response[0:2])[0]
    flags = unpack('!H', response[2:4])[0]
    qdCount = unpack('!H', response[4:6])[0]
    anCount = unpack('!H', response[6:8])[0]
    nsCount = unpack('!H', response[8:10])[0]
    arCount = unpack('!H', response[10:12])[0]

    # Flag bit manipulation
    aaFlag = ((flags & 0x0400) != 0)
    rcFlag = (flags & 15)

    # create list of tuples with servername and end index
    print('here are the server names')
    server_names = getServerNames(response, nsCount)
    server_ips = getServerIps(response, server_names, arCount)
    
    for i in range(0, len(server_ips)):
        print(server_ips[i])

    print(server_ips)
    print('nsCount: ' + str(nsCount) + 'arCount: ' + str(arCount))
    return server_ips


def resolved(response):
    '''
    Checks if there are any answers
    '''
    anCount = unpack('!H', response[6:8])[0]
    if anCount > 0: 
        print('answer is here')
        ans_start = networkToString(response, 12)[1] + 15
        print(ans_start)
        return getIp(response, ans_start)
    return None 


def getIp(response, answerStart):
    '''
    This is the ip address you are looking for
    DO THIS THING
    '''
    print('Question index')
    ans_index = networkToString(response, 12)[1] + 4
    #  ans_index = ans_name[1]
    #  print(ans_name)
    print(ans_index)
    ans_type = unpack('!H', response[ans_index+2:ans_index + 4])[0]
    print('ans_type\t' + str(ans_type))
    #  data_length = unpack('!H', response[answerStart + 10:answerStart + 12])[0]
    data_length = unpack('!H', response[ans_index + 8:ans_index + 10])[0]
    print('data_length\t' + str(data_length))
    #  answer_tuple = [networkToString(response, ans_name[1] + 12)]
   #if ans_type = 1:
     
    """
    question = networkToString(response, 12)
    server_name_tuples = [networkToString(response, question[1] + 16)]
    for i in range(nsCount-1):
        server_name_tuples.append(
                networkToString(response, server_name_tuples[i][1] + 12))
    servers_name_list = [x[0] for x in server_name_tuples]

    """

    ''' NEED TO GET THE FINAL THING HERE ''' 
    #  while data_length != 4:
    #      data_length = unpack('!H', response[ans_index - 2:ans_index])
    #      print('inside loops')
    #      print(data_length)
    return  'hello'
    #  return socket.inet_ntoa(response[ans_index:ans_index+4])


def sendAndReceive(sock, port, query, servers):
    for ip_addr in servers:
        try:
            sock.sendto(query, (ip_addr, 53))
            response = sock.recv(4096)

            # check if resolved
            name = resolved(response)
            if name is not None: # we've got a response
                print(name)
                sys.exit(1)
                return name
                print(name)

            # if we got servers; search them
            new_servers = unpackResponse(response)

            # recursive call
            sendAndReceive(sock, port, query, new_servers)
        except socket.timeout as e:
            print("Exception:", e)
        #  break

def main(argv=None):
    if argv is None:
        argv = sys.argv

    args = parseArgs()

    with open('root-servers.txt') as f:
        servers = f.read().splitlines()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)   # socket should timeout after 5 seconds

    id = random.randint(0, 65535)
    query = constructQuery(id, args.host_ip)

    # the sexy recursive function
    name = sendAndReceive(sock, 53, query, servers)


if __name__ == "__main__":
    sys.exit(main())
