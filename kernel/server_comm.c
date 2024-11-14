#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <net/sock.h>
#include <linux/string.h>
#include "server_comm.h"

// Global variable definition
struct sock *nl_sk = NULL;

static void nl_recv_msg(struct sk_buff *skb)
{
    struct nlmsghdr *nlh;
    struct server_msg *msg;
    int pid;
    struct sk_buff *skb_out;
    
    nlh = (struct nlmsghdr *)skb->data;
    pid = nlh->nlmsg_pid;
    
    // Process received message
    msg = (struct server_msg *)nlmsg_data(nlh);
    SERVER_COMM_INFO("Received code: %s", msg->code);
    SERVER_COMM_INFO("Received content: %s", msg->content);
    
    // Prepare response
    skb_out = nlmsg_new(sizeof(struct server_msg), 0);
    if (!skb_out) {
        SERVER_COMM_ERROR("Failed to allocate new skb");
        return;
    }
    
    nlh = nlmsg_put(skb_out, 0, 0, NLMSG_DONE, sizeof(struct server_msg), 0);
    msg = nlmsg_data(nlh);
    strscpy(msg->code, MSG_SUCCESS, sizeof(msg->code));
    strscpy(msg->content, "Message received by kernel", sizeof(msg->content));
    
    nlmsg_unicast(nl_sk, skb_out, pid);
}

static int __init server_comm_init(void)
{
    struct netlink_kernel_cfg cfg = {
        .input = nl_recv_msg,
    };
    
    nl_sk = netlink_kernel_create(&init_net, NETLINK_USER, &cfg);
    if (!nl_sk) {
        SERVER_COMM_ERROR("Error creating netlink socket");
        return -10;
    }
    
    SERVER_COMM_INFO("Module initialized");
    return 0;
}

static void __exit server_comm_exit(void)
{
    netlink_kernel_release(nl_sk);
    SERVER_COMM_INFO("Module unloaded");
}

module_init(server_comm_init);
module_exit(server_comm_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Server Communication Kernel Module"); 