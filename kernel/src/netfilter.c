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
 * extract_dns_query - Extract queried domain from DNS packet
 * @skb: Socket buffer containing the DNS packet
 * @domain: Buffer to store the extracted domain name
 * @maxlen: Maximum length of domain buffer
 *
 * Extracts and parses the queried domain name from a DNS packet.
 * Validates UDP and DNS headers before attempting extraction.
 *
 * Return: Length of extracted domain name on success, -1 on failure
 */
static int extract_dns_query(struct sk_buff *skb, char *domain, int maxlen) {
    struct udphdr *udp;
    struct dns_header *dns;
    unsigned char *data;

    udp = udp_hdr(skb);
    if (!udp)
        return -1;

    dns = (struct dns_header *)(udp + 1);
    if (!dns)
        return -1;

    data = (unsigned char *)(dns + 1);
    int ret = parse_domain_name(data, domain, maxlen);

    return ret;
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
 * pre_routing_hook - Netfilter hook for DNS request filtering
 * @priv: Private data (unused)
 * @skb: Socket buffer containing the packet
 * @state: Netfilter hook state
 *
 * Main packet filtering function that:
 * 1. Identifies DNS queries
 * 2. Extracts queried domain name
 * 3. Checks domain against blocklist
 * 4. Returns NXDOMAIN for blocked domains
 *
 * Return: NF_ACCEPT to allow packet, NF_DROP for blocked domains
 */
static unsigned int pre_routing_hook(void *priv,
                                   struct sk_buff *skb,
                                   const struct nf_hook_state *state) {
    struct iphdr *ip_header;
    char domain[MAX_DOMAIN_LENGTH];
    
    if (!skb || !(ip_header = ip_hdr(skb)))
        return NF_ACCEPT;

    if (ip_header->protocol != IPPROTO_UDP || !is_dns_query(skb))
        return NF_ACCEPT;

    if (extract_dns_query(skb, domain, sizeof(domain)) <= 0)
        return NF_ACCEPT;

    if (is_domain_blocked(domain)) {
        printk(KERN_INFO MODULE_NAME ": Blocking access to domain: %s\n", domain);
        block_dns_response(skb);
        return NF_DROP;
    }

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
