#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include "utils.h"
#include "cache.h"
#include "netfilter.h"
#include "network.h"

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Domain Blocking Kernel Module");
MODULE_VERSION("1.0");

static int __init network_filter_init(void) {
    int ret;

    printk(KERN_INFO MODULE_NAME ": Initializing module\n");

    ret = init_cache();
    if (ret < 0) {
        printk(KERN_ERR MODULE_NAME ": Failed to initialize cache\n");
        goto fail;
    }

    ret = init_netfilter();
    if (ret < 0) {
        printk(KERN_ERR MODULE_NAME ": Failed to initialize netfilter\n");
        goto fail_netfilter;
    }

    ret = init_network();
    if (ret < 0) {
        printk(KERN_ERR MODULE_NAME ": Failed to initialize network\n");
        goto fail_network;
    }

    printk(KERN_INFO MODULE_NAME ": Module initialized successfully\n");
    return 0;

fail_network:   cleanup_netfilter();
fail_netfilter: cleanup_cache();
fail:           return ret;
}

static void __exit network_filter_exit(void) {
    printk(KERN_INFO MODULE_NAME ": Cleaning up module\n");
    cleanup_network();
    cleanup_netfilter();
    cleanup_cache();
    printk(KERN_INFO MODULE_NAME ": Module cleanup complete\n");
}

module_init(network_filter_init);
module_exit(network_filter_exit);
