#include "cache.h"

/* Global variables */
DEFINE_HASHTABLE(domain_cache, __HASH_SIZE);
DEFINE_SPINLOCK(__cache_lock);
struct settings_cache __settings;

/* Simple but effective domain hash function */
static unsigned int hash_domain(const char *domain)
{
    unsigned int hash = 0;
    while (*domain) {
        hash = hash * 31 + *domain;
        domain++;
    }
    return hash;
}

bool is_domain_blocked(const char *domain) {
    unsigned int hash = hash_domain(domain);
    struct domain_entry *entry;
    bool found = false;

    rcu_read_lock();
    hash_for_each_possible_rcu(domain_cache, entry, node, hash) {
        if (strcmp(entry->domain, domain) == 0) {
            found = true;
            break;
        }
    }
    rcu_read_unlock();

    printk(KERN_DEBUG MODULE_NAME ": Domain %s is %s\n", 
           domain, found ? "blocked" : "not blocked");
    return found;
}

void add_domain_to_cache(const char *domain) {
    struct domain_entry *entry = NULL;
    unsigned int hash = hash_domain(domain);

    entry = kmalloc(sizeof(*entry), GFP_KERNEL);
    if (!entry) {
        printk(KERN_ERR MODULE_NAME ": Failed to allocate domain entry\n");
        return;
    }

    entry->domain = kstrdup(domain, GFP_KERNEL);
    if (!entry->domain) {
        printk(KERN_ERR MODULE_NAME ": Failed to allocate domain string\n");
        kfree(entry);
        return;
    }

    spin_lock(&__cache_lock);
    hash_add_rcu(domain_cache, &entry->node, hash);
    spin_unlock(&__cache_lock);

    printk(KERN_INFO MODULE_NAME ": Added domain %s to cache\n", domain);
}

void remove_domain_from_cache(const char *domain) {
    struct domain_entry *entry;
    unsigned int hash = hash_domain(domain);
    struct hlist_node *tmp;
    struct domain_entry *found_entry = NULL;

    spin_lock(&__cache_lock);
    hash_for_each_possible_safe(domain_cache, entry, tmp, node, hash) {
        if (strcmp(entry->domain, domain) == 0) {
            hash_del_rcu(&entry->node);
            found_entry = entry;
            break;
        }
    }
    spin_unlock(&__cache_lock);

    if (found_entry) {
        synchronize_rcu();
        kfree(found_entry->domain);
        kfree(found_entry);
    }
    printk(KERN_INFO MODULE_NAME ": Removed domain %s from cache\n", domain);
}

void update_settings(bool ad_block, bool adult_block) {
    spin_lock(&__cache_lock);
    __settings.ad_block_enabled = ad_block;
    __settings.adult_content_enabled = adult_block;
    spin_unlock(&__cache_lock);

    printk(KERN_INFO MODULE_NAME ": Settings updated - Ad block: %s, Adult block: %s\n",
           ad_block ? "on" : "off", adult_block ? "on" : "off");
}

int init_cache(void) {
    hash_init(domain_cache);
    __settings.ad_block_enabled = false;
    __settings.adult_content_enabled = false;
    printk(KERN_INFO MODULE_NAME ": Cache initialized\n");
    return 0;
}

void cleanup_cache(void) {
    struct domain_entry *entry;
    struct hlist_node *tmp;
    unsigned int bkt;
    int count = 0;

    spin_lock(&__cache_lock);
    hash_for_each_safe(domain_cache, bkt, tmp, entry, node) {
        hash_del(&entry->node);
        kfree(entry->domain);
        kfree(entry);
        count++;
    }
    spin_unlock(&__cache_lock);
    printk(KERN_INFO MODULE_NAME ": Cleaned up %d cache entries\n", count);
}
