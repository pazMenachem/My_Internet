// main.c
#include "domain_blocker.h"

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Domain Blocking Kernel Module");
MODULE_VERSION("1.0");

static int __init domain_blocker_init(void) {
    int ret;

    printk(KERN_INFO "Domain Blocker: Initializing module\n");

    ret = init_cache();
    if (ret < 0) {
        printk(KERN_ERR "Domain Blocker: Failed to initialize cache\n");
        return ret;
    }

    ret = init_netfilter();
    if (ret < 0) {
        printk(KERN_ERR "Domain Blocker: Failed to initialize netfilter\n");
        cleanup_cache();
        return ret;
    }

    ret = init_network();
    if (ret < 0) {
        printk(KERN_ERR "Domain Blocker: Failed to initialize network\n");
        cleanup_netfilter();
        cleanup_cache();
        return ret;
    }

    printk(KERN_INFO "Domain Blocker: Module initialized successfully\n");
    return 0;
}

static void __exit domain_blocker_exit(void) {
    printk(KERN_INFO "Domain Blocker: Cleaning up module\n");
    cleanup_network();
    cleanup_netfilter();
    cleanup_cache();
    printk(KERN_INFO "Domain Blocker: Module cleanup complete\n");
}

module_init(domain_blocker_init);
module_exit(domain_blocker_exit);
