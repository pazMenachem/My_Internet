#include "cache.h"

/* Global variables */
static DEFINE_HASHTABLE(domain_cache, HASH_SIZE);
DEFINE_SPINLOCK(cache_lock);
static struct settings_cache settings;

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

    return found;
}

void add_domain_to_cache(const char *domain) {
    struct domain_entry *entry;
    unsigned int hash = hash_domain(domain);

    entry = kmalloc(sizeof(*entry), GFP_KERNEL);
    if (!entry)
        return;

    entry->domain = kstrdup(domain, GFP_KERNEL);
    if (!entry->domain) {
        kfree(entry);
        return;
    }

    spin_lock(&cache_lock);
    hash_add_rcu(domain_cache, &entry->node, hash);
    spin_unlock(&cache_lock);
}

void remove_domain_from_cache(const char *domain) {
    struct domain_entry *entry;
    unsigned int hash = hash_domain(domain);
    struct hlist_node *tmp;
    struct domain_entry *found_entry = NULL;

    spin_lock(&cache_lock);
    hash_for_each_possible_safe(domain_cache, entry, tmp, node, hash) {
        if (strcmp(entry->domain, domain) == 0) {
            hash_del_rcu(&entry->node);
            found_entry = entry;
            break;
        }
    }
    spin_unlock(&cache_lock);

    if (found_entry) {
        synchronize_rcu();
        kfree(found_entry->domain);
        kfree(found_entry);
    }
}

void update_settings(bool ad_block, bool adult_block) {
    spin_lock(&cache_lock);
    settings.ad_block_enabled = ad_block;
    settings.adult_content_enabled = adult_block;
    spin_unlock(&cache_lock);
}

int init_cache(void) {
    hash_init(domain_cache);
    settings.ad_block_enabled = false;
    settings.adult_content_enabled = false;
    return 0;
}

void cleanup_cache(void) {
    struct domain_entry *entry;
    struct hlist_node *tmp;
    unsigned int bkt;

    spin_lock(&cache_lock);
    hash_for_each_safe(domain_cache, bkt, tmp, entry, node) {
        hash_del(&entry->node);
        kfree(entry->domain);
        kfree(entry);
    }
    spin_unlock(&cache_lock);
}
