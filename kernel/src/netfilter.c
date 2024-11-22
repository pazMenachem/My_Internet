#include "netfilter.h"

/* Netfilter hook operations */
static struct nf_hook_ops nfho_pre_routing;
static struct nf_hook_ops nfho_local_out;

/* DNS packet handling functions */
static int parse_dns_name(unsigned char *src, char *dst, int max_len)
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

static bool is_dns_query(struct sk_buff *skb) {
    struct udphdr *udp;
    struct dns_header *dns;

    udp = udp_hdr(skb);
    if (!udp || ntohs(udp->dest) != 53)
        return false;

    dns = (struct dns_header *)(udp + 1);
    return dns && ntohs(dns->q_count) > 0;
}

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
    int ret = parse_dns_name(data, domain, maxlen);
    printk(KERN_DEBUG MODULE_NAME ": Extracted DNS query: %s (ret=%d)\n", 
           ret > 0 ? domain : "failed", ret);
    return ret;
}

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

static unsigned int pre_routing_hook(void *priv,
                                   struct sk_buff *skb,
                                   const struct nf_hook_state *state) {
    struct iphdr *ip_header;
    char domain[MAX_DOMAIN_LENGTH];
    
    if (!skb || !(ip_header = ip_hdr(skb)))
        return NF_ACCEPT;

    // Only process UDP DNS packets
    if (ip_header->protocol != IPPROTO_UDP || !is_dns_query(skb))
        return NF_ACCEPT;

    // Extract domain name from DNS query
    if (extract_dns_query(skb, domain, sizeof(domain)) <= 0)
        return NF_ACCEPT;

    // Check if domain is blocked
    if (is_domain_blocked(domain)) {
        printk(KERN_INFO MODULE_NAME ": Blocking access to domain: %s\n", domain);
        block_dns_response(skb);
        return NF_DROP;
    }

    return NF_ACCEPT;
}

static unsigned int local_out_hook(void *priv,
                                 struct sk_buff *skb,
                                 const struct nf_hook_state *state) {
    struct iphdr *ip_header;
    struct udphdr *udp;
    struct settings_cache current_settings;
    
    if (!skb || !(ip_header = ip_hdr(skb)))
        return NF_ACCEPT;

    // Only intercept UDP DNS queries (port 53)
    if (ip_header->protocol != IPPROTO_UDP || 
        !(udp = udp_hdr(skb)) || 
        ntohs(udp->dest) != 53)
        return NF_ACCEPT;

    spin_lock(&__cache_lock);
    current_settings = __settings;
    spin_unlock(&__cache_lock);

    // Only redirect if filtering is enabled
    if (!current_settings.ad_block_enabled && !current_settings.adult_content_enabled)
        return NF_ACCEPT;

    // Select appropriate DNS server
    if (current_settings.ad_block_enabled && current_settings.adult_content_enabled) {
        ip_header->daddr = in_aton(ADGUARD_FAMILY_DNS);
        printk(KERN_DEBUG MODULE_NAME ": Using ADGUARD_FAMILY_DNS for both filters\n");
    } else if (current_settings.ad_block_enabled) {
        ip_header->daddr = in_aton(ADGUARD_DNS);
        printk(KERN_DEBUG MODULE_NAME ": Using ADGUARD_DNS for ad blocking\n");
    } else if (current_settings.adult_content_enabled) {
        ip_header->daddr = in_aton(CLOUDFLARE_DNS);
        printk(KERN_DEBUG MODULE_NAME ": Using CLOUDFLARE_DNS for adult content\n");
    }

    // Recalculate checksum
    ip_header->check = 0;
    ip_header->check = ip_fast_csum((unsigned char *)ip_header, ip_header->ihl);

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

    nfho_local_out.hook = local_out_hook;
    nfho_local_out.hooknum = NF_INET_LOCAL_OUT;
    nfho_local_out.pf = PF_INET;
    nfho_local_out.priority = NF_IP_PRI_FIRST;

    ret = nf_register_net_hook(&init_net, &nfho_local_out);
    if (ret < 0) {
        nf_unregister_net_hook(&init_net, &nfho_pre_routing);
        printk(KERN_ERR MODULE_NAME ": Failed to register local out hook\n");
        return ret;
    }
    printk(KERN_INFO MODULE_NAME ": Netfilter hooks registered\n");

    return 0;
}

void cleanup_netfilter(void) {
    nf_unregister_net_hook(&init_net, &nfho_pre_routing);
    nf_unregister_net_hook(&init_net, &nfho_local_out);
    printk(KERN_INFO MODULE_NAME ": Netfilter hooks cleaned up\n");
}
