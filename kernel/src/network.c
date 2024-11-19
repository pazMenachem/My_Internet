#include "network.h"

/* Private definitions */
static struct socket *server_socket = NULL;
static struct task_struct *connection_thread = NULL;
static bool module_running = true;

/**
 * process_server_message - Process incoming JSON messages from server
 * @buffer: Null-terminated string containing JSON message
 *
 * Parses JSON messages and executes corresponding actions:
 * - Update ad blocking settings
 * - Update adult content settings
 * - Add/remove domains from cache
 * - Update initial settings
 *
 * Return: 0 on success, negative on error
 */
static bool validate_message(const char *buffer) {
    return strstr(buffer, "\"" STR_CODE "\":\"" CODE_SUCCESS "\"") != NULL;
}

static bool handle_ad_block_settings(const char *buffer) {
    if (!strstr(buffer, "\"" STR_OPERATION "\":\"" CODE_AD_BLOCK "\"")) {
        return false;
    }

    const char *content = strstr(buffer, "\"" STR_CONTENT "\":\"");
    if (content) {
        bool enabled = strstr(content, "on") != NULL;
        update_settings(enabled, __settings.adult_content_enabled);
        printk(KERN_INFO "Network Filter: Ad blocking %s\n", 
               enabled ? "enabled" : "disabled");
    }
    return true;
}

static bool handle_adult_content_settings(const char *buffer) {
    if (!strstr(buffer, "\"" STR_OPERATION "\":\"" CODE_ADULT_BLOCK "\"")) {
        return false;
    }

    const char *content = strstr(buffer, "\"" STR_CONTENT "\":\"");
    if (content) {
        bool enabled = strstr(content, "on") != NULL;
        update_settings(__settings.ad_block_enabled, enabled);
        printk(KERN_INFO "Network Filter: Adult content blocking %s\n", 
               enabled ? "enabled" : "disabled");
    }
    return true;
}

static bool extract_domain(const char *content, char *domain, size_t max_len) {
    if (!content) return false;
    
    content += strlen("\"" STR_CONTENT "\":\"");
    const char *end = strchr(content, '"');
    if (!end || (end - content) >= max_len) return false;

    strncpy(domain, content, end - content);
    domain[end - content] = '\0';
    return true;
}

static bool handle_domain_operation(const char *buffer, bool is_add) {
    const char *operation = is_add ? CODE_ADD_DOMAIN : CODE_REMOVE_DOMAIN;
    if (!strstr(buffer, "\"" STR_OPERATION "\":\"")) {
        return false;
    }

    char domain[MAX_DOMAIN_LENGTH];
    const char *content = strstr(buffer, "\"" STR_CONTENT "\":\"");
    
    if (extract_domain(content, domain, MAX_DOMAIN_LENGTH)) {
        if (is_add) {
            add_domain_to_cache(domain);
            printk(KERN_INFO "Network Filter: Added domain %s\n", domain);
        } else {
            remove_domain_from_cache(domain);
            printk(KERN_INFO "Network Filter: Removed domain %s\n", domain);
        }
        return true;
    }
    return false;
}

static bool handle_initial_settings(const char *buffer) {
    if (!strstr(buffer, "\"" STR_OPERATION "\":\"" CODE_INIT_SETTINGS "\"")) {
        return false;
    }

    const char *content = strstr(buffer, "\"" STR_CONTENT "\":");
    if (content) {
        bool ad_block = strstr(content, "\"" STR_AD_BLOCK "\":\"on\"") != NULL;
        bool adult_block = strstr(content, "\"" STR_ADULT_BLOCK "\":\"on\"") != NULL;
        update_settings(ad_block, adult_block);
        printk(KERN_INFO "Network Filter: Initial settings - Ad block: %s, Adult block: %s\n",
               ad_block ? "on" : "off", adult_block ? "on" : "off");
        return true;
    }
    return false;
}

static int process_server_message(const char *buffer) {
    if (!validate_message(buffer)) {
        return 0;
    }

    if (handle_ad_block_settings(buffer)        ||
        handle_adult_content_settings(buffer)   ||
        handle_domain_operation(buffer, true)   ||  // Add domain
        handle_domain_operation(buffer, false)  ||  // Remove domain
        handle_initial_settings(buffer)) {
        return 0;
    }

    return -EINVAL;  // Invalid or unhandled message type
}

static int connection_handler(void *data) {
    struct socket *sock = server_socket;
    char *buffer;
    struct msghdr msg;
    struct kvec iov;
    int ret;

    buffer = kmalloc(MAX_PAYLOAD, GFP_KERNEL);
    if (!buffer)
        return -ENOMEM;

    while (module_running) {
        memset(&msg, 0, sizeof(msg));
        iov.iov_base = buffer;
        iov.iov_len = MAX_PAYLOAD - 1;

        ret = kernel_recvmsg(sock, &msg, &iov, 1, MAX_PAYLOAD - 1, 0);
        if (ret > 0) {
            buffer[ret] = '\0';
            process_server_message(buffer);
        }
        else if (ret < 0) {
            break;
        }
    }

    kfree(buffer);
    return 0;
}

int init_network(void) {
    struct sockaddr_in server_addr;
    int ret;

    ret = sock_create(AF_INET, SOCK_STREAM, IPPROTO_TCP, &server_socket);
    if (ret < 0) {
        printk(KERN_ERR "Network Filter: Failed to create socket\n");
        return ret;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    server_addr.sin_addr.s_addr = in_aton(SERVER_IP);

    ret = kernel_connect(server_socket, (struct sockaddr *)&server_addr, 
                        sizeof(server_addr), 0);
    if (ret < 0) {
        printk(KERN_ERR "Network Filter: Failed to connect to server\n");
        sock_release(server_socket);
        return ret;
    }

    connection_thread = kthread_run(connection_handler, NULL, "Network Filter_conn");
    if (IS_ERR(connection_thread)) {
        printk(KERN_ERR "Network Filter: Failed to create connection thread\n");
        sock_release(server_socket);
        return PTR_ERR(connection_thread);
    }

    return 0;
}

void cleanup_network(void) {
    module_running = false;
    if (connection_thread)
        kthread_stop(connection_thread);
    if (server_socket)
        sock_release(server_socket);
}
