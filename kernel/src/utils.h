#ifndef UTILS_H
#define UTILS_H

#include <linux/types.h>

/* Module name definition */
#define MODULE_NAME "Network_Filter"

#define __HASH_SIZE               8
#define MAX_DOMAIN_LENGTH       256
#define MAX_PAYLOAD             1024
#define SERVER_PORT             65433
#define SERVER_IP               "127.0.0.1"

// Message codes matching server's utils.py
#define CODE_AD_BLOCK           "50"
#define CODE_ADULT_BLOCK        "51"
#define CODE_ADD_DOMAIN         "52"
#define CODE_REMOVE_DOMAIN      "53"
#define CODE_DOMAIN_LIST_UPDATE "54"
#define CODE_INIT_SETTINGS      "55"
#define CODE_SUCCESS            "100"
#define CODE_ERROR              "101"

#define CODE_AD_BLOCK_INT      50
#define CODE_ADULT_BLOCK_INT   51
#define CODE_ADD_DOMAIN_INT    52
#define CODE_REMOVE_DOMAIN_INT 53
#define CODE_INIT_SETTINGS_INT 55

// JSON field names matching server's utils.py
#define STR_CODE                "code"
#define STR_CONTENT             "content"
#define STR_OPERATION           "operation"
#define STR_AD_BLOCK            "ad_block"
#define STR_ADULT_BLOCK         "adult_block"
#define STR_DOMAINS             "domains"
#define STR_SETTINGS            "settings"

/* DNS Server configurations */
#define ADGUARD_DNS             "94.140.14.14"
#define CLOUDFLARE_DNS          "1.1.1.3"
#define ADGUARD_FAMILY_DNS      "94.140.14.15"

// DNS response flags
#define DNS_RESPONSE     0x8000
#define DNS_NXDOMAIN    0x0003

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
