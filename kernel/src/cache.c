#include "cache.h"

/* Global variables */
DEFINE_HASHTABLE(domain_cache, __HASH_SIZE);
DEFINE_SPINLOCK(__cache_lock);

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

int init_cache(void) {
    hash_init(domain_cache);
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

int parse_domains(const char *buffer) {
    const char *value_start;
    size_t value_len;
    int ret = get_json_value(buffer, STR_DOMAINS, &value_start, &value_len);
    
    if (ret < 0) {
        printk(KERN_WARNING MODULE_NAME ": Failed to find domains array: %d\n", ret);
        return ret;
    }

    char domain[MAX_DOMAIN_LENGTH];
    value_start++;
    const char *end;
    int count_domains = 0;

    while (*value_start != ']') {
        value_start++; // Skip opening quote
        end = strchr(value_start, '"');
        if (!end) break;

        size_t len = end - value_start;
        if (len >= MAX_DOMAIN_LENGTH) {
            printk(KERN_WARNING MODULE_NAME ": Domain too long, skipping\n");
            value_start = end + 1;
            continue;
        }

        memcpy(domain, value_start, len);
        domain[len] = '\0';
        add_domain_to_cache(domain);
        
        value_start = end + 1;
        count_domains++;
    }

    printk(KERN_INFO MODULE_NAME ": Initialized with %d domains\n", count_domains);
    return count_domains;
}
