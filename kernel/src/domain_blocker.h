#ifndef DOMAIN_BLOCKER_H
#define DOMAIN_BLOCKER_H

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/net.h>
#include <linux/socket.h>
#include <linux/tcp.h>
#include <linux/in.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/udp.h>
#include <linux/string.h>
#include <linux/kthread.h>
#include <linux/slab.h>
#include <linux/hashtable.h>
#include <linux/rculist.h>
#include <linux/spinlock.h>
#include <linux/skbuff.h>
#include <linux/netdevice.h>
#include <net/netfilter/nf_socket.h>

#define SERVER_PORT 65433
#define SERVER_IP "127.0.0.1"
#define MAX_PAYLOAD 1024
#define HASH_SIZE 8  // 2^8 = 256 buckets
#define MAX_DOMAIN_LENGTH 256

// Message codes matching server's utils.py
#define CODE_AD_BLOCK           "50"
#define CODE_ADULT_BLOCK        "51"
#define CODE_ADD_DOMAIN         "52"
#define CODE_REMOVE_DOMAIN      "53"
#define CODE_DOMAIN_LIST_UPDATE "54"
#define CODE_INIT_SETTINGS      "55"
#define CODE_SUCCESS            "100"
#define CODE_ERROR             "101"

// JSON field names matching server's utils.py
#define STR_CODE       "code"
#define STR_CONTENT    "content"
#define STR_OPERATION  "operation"

// DNS structures
struct dns_header {
    __u16 id;
    __u16 flags;
    __u16 q_count;
    __u16 ans_count;
    __u16 auth_count;
    __u16 add_count;
};

struct dns_question {
    __u16 qtype;
    __u16 qclass;
};

// Cache structures
struct domain_entry {
    struct hlist_node node;
    char *domain;
    struct rcu_head rcu;
};

struct settings_cache {
    bool ad_block_enabled;
    bool adult_content_enabled;
};

// Function declarations
bool is_domain_blocked(const char *domain);
void add_domain_to_cache(const char *domain);
void remove_domain_from_cache(const char *domain);
void update_settings(bool ad_block, bool adult_block);
int init_cache(void);
void cleanup_cache(void);
int init_netfilter(void);
void cleanup_netfilter(void);
int init_network(void);
void cleanup_network(void);

#endif // DOMAIN_BLOCKER_H
