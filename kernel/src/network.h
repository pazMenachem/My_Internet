#ifndef NETWORK_H
#define NETWORK_H

#include <linux/net.h>
#include <linux/socket.h>
#include <linux/tcp.h>
#include <net/netfilter/nf_socket.h>
#include "utils.h"
#include "cache.h"

/**
 * init_network - Initialize network connection to management server
 *
 * Creates TCP socket, connects to management server and starts
 * connection handler thread for receiving commands.
 *
 * Context: Process context only (may sleep)
 *
 * Return: 0 on success, negative error code on failure
 */
int init_network(void);

/**
 * cleanup_network - Clean up network resources
 *
 * Stops connection handler thread and releases socket.
 * Should be called during module cleanup.
 *
 * Context: Process context only (may sleep)
 */
void cleanup_network(void);

#endif /* NETWORK_H */ 