#ifndef UTILS_H
#define UTILS_H

#include <linux/types.h>

#define HASH_SIZE            8
#define MAX_DOMAIN_LENGTH    256
#define MAX_PAYLOAD         1024

/* DNS Server configurations */
#define ADGUARD_DNS         "94.140.14.14"
#define CLOUDFLARE_DNS      "1.1.1.3"
#define ADGUARD_FAMILY_DNS  "94.140.14.15"

/* Common structures used across modules */
struct dns_header {
    __u16 id;
    __u16 flags;
    __u16 q_count;
    __u16 ans_count;
    __u16 auth_count;
    __u16 add_count;
};

struct dns_question {
    __u16 qtype;
    __u16 qclass;
};

#endif /* UTILS_H */
