#ifndef SERVER_COMM_H
#define SERVER_COMM_H

#include <linux/netlink.h>
#include <linux/skbuff.h>

#define NETLINK_USER 31
#define MAX_PAYLOAD 1024

// Message structure for communication
struct server_msg {
    char code[32];
    char content[MAX_PAYLOAD];
};

// Function prototypes
static void nl_recv_msg(struct sk_buff *skb);
static int __init server_comm_init(void);
static void __exit server_comm_exit(void);

// Global variables declaration
extern struct sock *nl_sk;

// Message status codes
#define MSG_SUCCESS "success"
#define MSG_FAILED "failed"

// Debug macros
#ifdef DEBUG
    #define SERVER_COMM_DEBUG(fmt, ...) \
        printk(KERN_DEBUG "Server Comm: " fmt "\n", ##__VA_ARGS__)
#else
    #define SERVER_COMM_DEBUG(fmt, ...) \
        do {} while (0)
#endif

#define SERVER_COMM_ERROR(fmt, ...) \
    printk(KERN_ERR "Server Comm Error: " fmt "\n", ##__VA_ARGS__)

#define SERVER_COMM_INFO(fmt, ...) \
    printk(KERN_INFO "Server Comm: " fmt "\n", ##__VA_ARGS__)

#endif /* SERVER_COMM_H */ 