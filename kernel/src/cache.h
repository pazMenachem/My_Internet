#ifndef CACHE_H
#define CACHE_H

#include <linux/hashtable.h>
#include <linux/spinlock.h>
#include <linux/rculist.h>
#include <linux/slab.h>
#include <linux/string.h>
#include "utils.h"
#include "json_parser.h"

extern spinlock_t __cache_lock;

/* Cache structures */
struct domain_entry {
    struct hlist_node node;
    char *domain;
    struct rcu_head rcu;
};

/**
 * is_domain_blocked - Check if a domain is in the blocking cache
 * @domain: Domain name to check
 *
 * Performs an RCU-safe lookup in the domain cache to determine
 * if the specified domain is blocked.
 *
 * Context: Any context (RCU read lock is held internally)
 *
 * Return: true if domain is blocked, false otherwise
 */
bool is_domain_blocked(const char *domain);

/**
 * add_domain_to_cache - Add a domain to the blocking cache
 * @domain: Domain name to add
 *
 * Adds a new domain to the RCU-protected domain cache.
 * Memory allocation may fail silently.
 *
 * Context: Process context only (may sleep)
 */
void add_domain_to_cache(const char *domain);

/**
 * remove_domain_from_cache - Remove a domain from the blocking cache
 * @domain: Domain name to remove
 *
 * Removes a domain from the RCU-protected domain cache if it exists.
 * Handles memory cleanup after RCU grace period.
 *
 * Context: Process context only (may sleep due to synchronize_rcu)
 */
void remove_domain_from_cache(const char *domain);

/**
 * init_cache - Initialize the domain cache
 *
 * Initializes the hash table for domain cache
 *
 * Context: Process context only
 *
 * Return: 0 on success, negative error code on failure
 */
int init_cache(void);

/**
 * cleanup_cache - Clean up the domain cache
 *
 * Frees all memory associated with cached domains and
 * cleans up the hash table.
 */
void cleanup_cache(void);

/**
 * parse_domains - Parse domains from JSON string
 * @buffer: JSON string containing domains
 * @example: "[ \"example.com\", \"example.org\" ]"
 *
 * Return: 0 on success, negative error code on failure
 */
int parse_domains(const char *buffer);

#endif /* CACHE_H */ 
