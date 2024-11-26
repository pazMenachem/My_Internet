#include "netfilter.h"

/* Netfilter hook operations */
static struct nf_hook_ops nfho_pre_routing;

/**
 * parse_domain_name - Parse DNS wire format domain name to string
 * @src: Source buffer containing DNS wire format name
 * @dst: Destination buffer for human-readable domain name
 * @max_len: Maximum length of destination buffer
 *
 * Converts DNS wire format domain name (length-prefixed labels) to a 
 * human-readable string. Handles DNS message compression (0xC0 pointer)
 * and removes .Home and .local suffixes. Each label is separated by dots.
 *
 * Example: [3]www[7]example[3]com[0] -> www.example.com
 *
 * Return: Length of parsed domain name on success, -1 if destination buffer too small
 */
static int parse_domain_name(unsigned char *src, char *dst, int max_len)
{
    int len = 0;
    int step;
    
    while (*src) {
        step = *src++;
        if (step >= max_len - len - 1)
            return -1;
            
        if (step == 0 || (step & 0xC0) == 0xC0)
            break;
            
        if (len)
            dst[len++] = '.';
            
        if (step > 0) {
            memcpy(dst + len, src, step);
            len += step;
            src += step;
        }
    }
    
    dst[len] = '\0';
    
    char *suffix = strstr(dst, ".Home");
    if (suffix)
        *suffix = '\0';
    suffix = strstr(dst, ".local");
    if (suffix)
        *suffix = '\0';
        
    return strlen(dst);
}

/**
 * is_dns_query - Check if packet is a DNS query
 * @skb: Socket buffer containing the packet
 *
 * Validates if the packet is a DNS query by checking:
 * 1. Valid UDP header exists
 * 2. Destination port is 53 (DNS)
 * 3. Valid DNS header exists with at least one question
 *
 * Return: true if packet is a valid DNS query, false otherwise
 */
static bool is_dns_query(struct sk_buff *skb) {
    struct udphdr *udp;
    struct dns_header *dns;

    udp = udp_hdr(skb);
    if (!udp || ntohs(udp->dest) != 53)
        return false;

    dns = (struct dns_header *)(udp + 1);
    return dns && ntohs(dns->q_count) > 0;
}

/**
 * extract_domain_from_response - Extract queried domain from DNS response
 * @udp: UDP header of the packet
 * @skb: Socket buffer containing the DNS response
 * @domain: Buffer to store the extracted domain name
 * @maxlen: Maximum length of domain buffer
 *
 * Extracts and parses the queried domain name from a DNS response packet.
 * Validates DNS header before attempting extraction.
 *
 * Return: Length of extracted domain name on success, -1 on failure
 */
static int extract_domain_from_response(const struct udphdr *udp, struct sk_buff *skb, 
                                      char *domain, int maxlen) {
    struct dns_header *dns;
    unsigned char *data;

    dns = (struct dns_header *)(udp + 1);
    if (!dns)
        return -1;

    data = (unsigned char *)(dns + 1);
    return parse_domain_name(data, domain, maxlen);
}

/**
 * block_dns_response - Modify DNS query to return NXDOMAIN
 * @skb: Socket buffer containing the DNS query
 *
 * Modifies the original DNS query in-place to create an NXDOMAIN response:
 * 1. Sets response and NXDOMAIN flags
 * 2. Clears all record counts
 * 3. Recalculates UDP checksum for modified packet
 *
 * Note: Assumes valid UDP and DNS headers, should be checked before calling
 */
static void block_dns_response(struct sk_buff *skb) {
    struct udphdr *udp;
    struct dns_header *dns;

    if (!(udp = udp_hdr(skb)) || !(dns = (struct dns_header *)(udp + 1)))
        return;

    // Set response flags for NXDOMAIN
    dns->flags |= htons(DNS_RESPONSE | DNS_NXDOMAIN);
    dns->ans_count = 0;
    dns->auth_count = 0;
    dns->add_count = 0;

    // Recalculate UDP checksum
    udp->check = 0;
    skb->csum = csum_partial((unsigned char *)udp, ntohs(udp->len), 0);
    udp->check = csum_tcpudp_magic(ip_hdr(skb)->saddr,
                                  ip_hdr(skb)->daddr,
                                  ntohs(udp->len),
                                  IPPROTO_UDP,
                                  skb->csum);
}

/**
 * check_dns_nxdomain - Check if DNS response is NXDOMAIN
 * @udp: UDP header of the packet
 * @skb: Socket buffer containing the DNS response
 *
 * Return: true if packet is NXDOMAIN response, false otherwise
 */
static bool check_dns_nxdomain(const struct udphdr *udp, struct sk_buff *skb) {
    struct dns_header *dns;
    uint16_t flags;

    dns = (struct dns_header *)(udp + 1);
    if (unlikely(!dns))
        return false;

    flags = ntohs(dns->flags);
    // check both response bit and NXDOMAIN in one comparison
    if ((flags & (DNS_RESPONSE | DNS_RCODE_MASK)) == (DNS_RESPONSE | DNS_NXDOMAIN)) {
        char domain[MAX_DOMAIN_LENGTH];

        if (extract_domain_from_response(udp, skb, domain, sizeof(domain)) > 0) {
            printk(KERN_INFO MODULE_NAME ": NXDOMAIN response for domain: %s\n", domain);
            return true;
        }
    }

    return false;
}

/**
 * handle_dns_response - Process DNS response for domain blocking
 * @skb: Socket buffer containing the packet
 * @udp: UDP header
 * @dns: DNS header
 * @domain: Extracted domain name
 *
 * Checks if domain is blocked and modifies response if needed.
 * Logs NXDOMAIN responses for monitoring.
 */
static void handle_dns_response(struct sk_buff *skb, 
                              const struct udphdr *udp,
                              const struct dns_header *dns,
                              const char *domain) {
    uint16_t flags = ntohs(dns->flags);
    bool is_blocked = is_domain_blocked(domain);

    if (is_blocked) 
        block_dns_response(skb);

    if (is_blocked || ((flags & (DNS_RESPONSE | DNS_RCODE_MASK)) == (DNS_RESPONSE | DNS_NXDOMAIN)))
        printk(KERN_INFO MODULE_NAME ": NXDOMAIN response for domain: %s%s\n",
               domain, is_blocked ? " (blocked)" : "");
}

/**
 * is_dns_response - Check if packet is a valid DNS response
 * @skb: Socket buffer containing the packet
 * @udp: Pointer to store UDP header
 * @dns: Pointer to store DNS header
 *
 * Validates packet headers and checks if it's a DNS response (port 53)
 *
 * Return: true if valid DNS response, false otherwise
 */
static bool is_dns_response(struct sk_buff *skb, struct udphdr **udp, struct dns_header **dns) {
    struct iphdr *ip_header;
    
    if (unlikely(!skb                               ||
                 !(ip_header = ip_hdr(skb))         || 
                 ip_header->protocol != IPPROTO_UDP ||
                 !(*udp = udp_hdr(skb))             ||
                 ntohs((*udp)->source) != 53        ||
                 !(*dns = (struct dns_header *)(*udp + 1))))
        return false;

    return true;
}

/**
 * pre_routing_hook - Netfilter hook for DNS response filtering
 * @priv: Private data (unused)
 * @skb: Socket buffer containing the packet
 * @state: Netfilter hook state
 *
 * Processes incoming DNS responses in pre-routing chain.
 * Modifies responses for blocked domains to return NXDOMAIN.
 *
 * Return: NF_ACCEPT always (modified or unmodified packet)
 */
static unsigned int pre_routing_hook(void *priv,
                                   struct sk_buff *skb,
                                   const struct nf_hook_state *state) {
    struct udphdr *udp;
    struct dns_header *dns;
    char domain[MAX_DOMAIN_LENGTH];
    
    if (!is_dns_response(skb, &udp, &dns))
        return NF_ACCEPT;

    if (extract_domain_from_response(udp, skb, domain, MAX_DOMAIN_LENGTH) <= 0)
        return NF_ACCEPT;

    handle_dns_response(skb, udp, dns, domain);

    return NF_ACCEPT;
}

int init_netfilter(void) {
    int ret = 0;

    nfho_pre_routing.hook = pre_routing_hook;
    nfho_pre_routing.hooknum = NF_INET_PRE_ROUTING;
    nfho_pre_routing.pf = PF_INET;
    nfho_pre_routing.priority = NF_IP_PRI_FIRST;

    ret = nf_register_net_hook(&init_net, &nfho_pre_routing);
    if (ret < 0) {
        printk(KERN_ERR MODULE_NAME ": Failed to register pre-routing hook\n");
        return ret;
    }

    printk(KERN_INFO MODULE_NAME ": Netfilter hooks registered\n");

    return 0;
}

void cleanup_netfilter(void) {
    nf_unregister_net_hook(&init_net, &nfho_pre_routing);
    printk(KERN_INFO MODULE_NAME ": Netfilter hooks cleaned up\n");
}
