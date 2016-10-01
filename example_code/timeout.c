/*
 *
 * File: timeout.c
 *
 * Example code for setting the timeout time of a socket.
 *
 * Compile using the following command:
 * 		gcc -Wall -O0 -g -o timeout timeout.c
 */

#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <string.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>


int main(int argc, char **argv) {
	int sock = socket(AF_INET, SOCK_DGRAM, 0);
	if (sock < 0) {
		perror("socket");
		exit(0);
	}

	/* Create a time value structure and set it to five seconds. */
	struct timeval tv;
	memset(&tv, 0, sizeof(struct timeval));
	tv.tv_sec = 5;

	/* Tell the OS to use that time value as a time out for operations on
	 * our socket. */
	int res = setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv,
			sizeof(struct timeval));

	if (res < 0) {
		perror("setsockopt");
		exit(0);
	}

	struct sockaddr_in addr;
	socklen_t len = sizeof(struct sockaddr_in);
	char buf[4096];

	/* Blocking calls will now return error (-1) after the timeout period with
	 * errno set to EAGAIN. */
	res = recvfrom(sock, buf, 4096, 0, (struct sockaddr *) &addr, &len);

	if (res < 1) {
		if (errno == EAGAIN) {
			printf("Timed out!\n");
		} else {
			perror("recv");
		}
	}

	return 0;
}
