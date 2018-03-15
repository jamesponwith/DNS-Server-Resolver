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
from startercode import stringToNetwork
from startercode import networkToString 
from startercode import constructQuery

def sendAndReceive(sock, port, query, servers):
    for ip_addr in servers:
        #  print('ip_addr\t' + str(ip_addr))
        try:
            sock.sendto(query, (ip_addr, 53))
            response = sock.recv(4096)

            aa, rc = getFlags(response)
            
            # check if resolved
            if aa is True:
                print(resolved(response))
                print('we resolved it')
                sys.exit(1)
                #  return resolved(response)

            #  if name is not None: # we've got a response
            #      print(name)
            #      sys.exit(1)
            #      return name
            #      print(name)

            # if we got servers; search them
            new_servers = unpackResponse(response)

            # recursive call
            sendAndReceive(sock, port, query, new_servers)
        except socket.timeout as e:
            print("Exception:", e)


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-m", "--mxlookup",  help="MX lookup", action="store_true")
    parser.add_argument("host_ip", help="Host name's IP address", type=str)
    args = parser.parse_args()
    return args


def getFlags(response):
    flags = unpack('!H', response[2:4])[0]
    # Flag bit manipulation
    # TODO: handle -MX requests
    aaFlag = ((flags & 0x0400) != 0)
    rcFlag = (flags & 15)
    return aaFlag, rcFlag



def unpackResponse(response):
    '''
    Unpacks the response for the list of server ips
    '''
    #  id = unpack('!H', response[0:2])[0]
    qdCount = unpack('!H', response[4:6])[0]
    anCount = unpack('!H', response[6:8])[0]
    nsCount = unpack('!H', response[8:10])[0]
    arCount = unpack('!H', response[10:12])[0]


    # create list of tuples with servername and end index
    server_names = getAuthNames(response, nsCount)
    server_ips = ipsFromAddtl(response, server_names, arCount)
    
    return server_ips


def getAuthNames(response, nsCount):
    '''
    Gets the list of server names as tuples
    we know where the authority rrs start from here
    '''
    question = networkToString(response, 12)

    server_names = [networkToString(response, question[1] + 16)]

    for i in range(nsCount-1):
        server_names.append(networkToString(response, server_names[i][1] + 12))

    #  servers_name_list = [x[0] for x in server_name_tuples]

    return server_names 


def ipsFromAddtl(response, server_name_tuples, arCount):
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


def resolved(response):
    '''
    Checks if there are any answers
    '''
    anCount = unpack('!H', response[6:8])[0]
    if anCount > 0: 
        ans_start = networkToString(response, 12)[1] + 15
        return getIp(response, ans_start)
    return None 


def getIp(response, answerStart):
    '''
    This is the ip address you are looking for
    '''
    ans_index = networkToString(response, 12)[1] + 4
    print(ans_index)
    ans_type = unpack('!H', response[ans_index+2:ans_index + 4])[0]
    if ans_type == 1:
        answer_string = socket.inet_ntoa(response[ans_index+12:ans_index +
            16])
        return answer_string
    else:
        num_ans = unpack('!H', response[6:8])[0]
        print(num_ans)
        if(num_ans == 1):
            print()
        else:
            print()

    while ans_type != 1:
        ans_index += 10 
        ans_index += unpack('!H', response[ans_index: ans_index + 2])[0]
        ans_index += 4
        ans_type = unpack('!H',response[ans_index:ans_index + 2])[0]
    ans_index += 8 
    data_length = unpack('!H', response[ans_index:ans_index + 2])[0]
    ans_index += 2
    return socket.inet_ntoa(response[ans_index:ans_index + data_length])    


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
    ip_addr = sendAndReceive(sock, 53, query, servers)
    #print('ip addr >>.')
    #print(ip_addr)

if __name__ == "__main__":
    sys.exit(main())
