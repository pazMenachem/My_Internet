#ifndef NETFILTER_H
#define NETFILTER_H

#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/udp.h>
#include <linux/skbuff.h>
#include <linux/types.h>
#include <linux/inet.h>
#include "utils.h"
#include "cache.h"

/* DNS packet handling structures */
struct dns_packet {
    struct udphdr *udp;
    struct dns_header *dns;
    unsigned char *data;
};

/**
 * init_netfilter - Initialize the netfilter hooks
 *
 * This function sets up and registers netfilter hooks:
 *  Pre-routing hook for intercepting incoming DNS queries
 *
 * Return: 0 on success, negative error code on failure
 */
int init_netfilter(void);

/**
 * cleanup_netfilter - Clean up and unregister netfilter hooks
 */
void cleanup_netfilter(void);

#endif /* NETFILTER_H */ 
