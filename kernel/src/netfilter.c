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
            
        if (len)
            dst[len++] = '.';
            
        if (step > 0) {
            memcpy(dst + len, src, step);
            len += step;
            src += step;
        }
    }
    
    dst[len] = '\0';
    return len;
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

    udp = udp_hdr(skb);
    if (!udp)
        return;

    dns = (struct dns_header *)(udp + 1);
    if (!dns)
        return;

    dns->flags |= htons(1 << 15);  // Set response bit
    dns->flags |= htons(3);        // Set "Name Error" response code
}

static unsigned int pre_routing_hook(void *priv,
                                   struct sk_buff *skb,
                                   const struct nf_hook_state *state) {
    struct iphdr *ip_header;
    char domain[MAX_DOMAIN_LENGTH];
    
    if (!skb)
        return NF_ACCEPT;

    ip_header = ip_hdr(skb);
    if (!ip_header)
        return NF_ACCEPT;

    if (ip_header->protocol == IPPROTO_UDP && is_dns_query(skb)) {
        if (extract_dns_query(skb, domain, sizeof(domain)) > 0) {
            if (is_domain_blocked(domain)) {
                block_dns_response(skb);
                return NF_DROP;
            }
        }
    }

    return NF_ACCEPT;
}

static unsigned int local_out_hook(void *priv,
                                 struct sk_buff *skb,
                                 const struct nf_hook_state *state) {
    struct iphdr *ip_header;
    struct udphdr *udp;
    struct settings_cache current_settings;
    
    if (!skb)
        return NF_ACCEPT;

    ip_header = ip_hdr(skb);
    if (!ip_header)
        return NF_ACCEPT;

    if (ip_header->protocol == IPPROTO_UDP) {
        udp = udp_hdr(skb);
        if (!udp || ntohs(udp->dest) != 53)
            return NF_ACCEPT;

        spin_lock(&__cache_lock);
        current_settings = __settings;
        spin_unlock(&__cache_lock);

        // Get current DNS server based on settings
        if (current_settings.ad_block_enabled && current_settings.adult_content_enabled) {
            printk(KERN_DEBUG MODULE_NAME ": Redirecting to ADGUARD_FAMILY_DNS\n");
            ip_header->daddr = in_aton(ADGUARD_FAMILY_DNS);
        } else if (current_settings.ad_block_enabled) {
            printk(KERN_DEBUG MODULE_NAME ": Redirecting to ADGUARD_DNS\n");
            ip_header->daddr = in_aton(ADGUARD_DNS);
        } else if (current_settings.adult_content_enabled) {
            printk(KERN_DEBUG MODULE_NAME ": Redirecting to CLOUDFLARE_DNS\n");
            ip_header->daddr = in_aton(CLOUDFLARE_DNS);
        } else {
            return NF_ACCEPT; // No filtering, use system DNS
        }

        ip_header->check = 0;
        ip_header->check = ip_fast_csum((unsigned char *)ip_header, ip_header->ihl);

        return NF_ACCEPT;
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
