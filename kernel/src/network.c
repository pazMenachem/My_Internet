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
    printk(KERN_DEBUG MODULE_NAME ": Validating message: %s\n", buffer);
    
    // More flexible validation that ignores whitespace
    char code_pattern[32];
    snprintf(code_pattern, sizeof(code_pattern), "\"%s\"", CODE_SUCCESS);
    
    const char *code_pos = strstr(buffer, code_pattern);
    bool valid = (code_pos != NULL);
    
    printk(KERN_DEBUG MODULE_NAME ": Looking for code pattern: %s\n", code_pattern);
    printk(KERN_DEBUG MODULE_NAME ": Message validation result: %s\n", valid ? "valid" : "invalid");
    
    return valid;
}

static bool handle_ad_block_settings(const char *buffer) {
    if (!strstr(buffer, "\"" STR_OPERATION "\":\"" CODE_AD_BLOCK "\""))
        return false;
    
    const char *content = strstr(buffer, "\"" STR_CONTENT "\":\"");
    if (content) {
        bool enabled = strstr(content, "on") != NULL;
        update_settings(enabled, __settings.adult_content_enabled);
        printk(KERN_INFO MODULE_NAME ": Ad blocking %s\n", 
               enabled ? "enabled" : "disabled");
    }
    return true;
}

static bool handle_adult_content_settings(const char *buffer) {
    const char *content = strstr(buffer, "\"" STR_CONTENT "\":\"");
    if (content) {
        bool enabled = strstr(content, "on") != NULL;
        update_settings(__settings.ad_block_enabled, enabled);
        printk(KERN_INFO MODULE_NAME ": Adult content blocking %s\n", 
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
    char domain[MAX_DOMAIN_LENGTH];
    const char *content = strstr(buffer, "\"" STR_CONTENT "\":\"");
    
    if (extract_domain(content, domain, MAX_DOMAIN_LENGTH)) {
        if (is_add) 
            add_domain_to_cache(domain);
        else 
            remove_domain_from_cache(domain);
        
        return true;
    }
    return false;
}

static bool parse_settings(const char *buffer) {
    const char *settings = strstr(buffer, "\"" STR_SETTINGS "\":");
    if (!settings) {
        printk(KERN_WARNING MODULE_NAME ": Settings object not found\n");
        return false;
    }

    bool ad_block = strstr(settings, "\"" STR_AD_BLOCK "\":\"on\"") != NULL;
    bool adult_block = strstr(settings, "\"" STR_ADULT_BLOCK "\":\"on\"") != NULL;
    update_settings(ad_block, adult_block);
    
    return true;
}

static bool parse_domains(const char *buffer) {
    const char *domains = strstr(buffer, "\"" STR_DOMAINS "\":[");
    if (!domains) {
        printk(KERN_WARNING MODULE_NAME ": Domains array not found\n");
        return false;
    }

    domains += strlen("\"" STR_DOMAINS "\":[");

    char domain[MAX_DOMAIN_LENGTH];
    const char *start = domains;
    const char *end;
    int count_domains = 0;

    while ((start = strchr(start, '"')) != NULL) {
        start++; // Skip opening quote
        end = strchr(start, '"');
        if (!end) break;

        size_t len = end - start;
        if (len >= MAX_DOMAIN_LENGTH) {
            printk(KERN_WARNING MODULE_NAME ": Domain too long, skipping\n");
            start = end + 1;
            continue;
        }

        memcpy(domain, start, len);
        domain[len] = '\0';
        add_domain_to_cache(domain);
        
        start = end + 1;
        count_domains++;
    }

    printk(KERN_INFO MODULE_NAME ": Initialized with %d domains\n", count_domains);
    return true;
}

static bool handle_initial_settings(const char *buffer) {
    return parse_settings(buffer) && parse_domains(buffer);
}

static int get_operation_code(const char *buffer) {
    printk(KERN_DEBUG MODULE_NAME ": Parsing operation from: %s\n", buffer);
    
    const char *op_str = strstr(buffer, "\"" STR_OPERATION "\":");
    if (!op_str) {
        printk(KERN_DEBUG MODULE_NAME ": Operation field not found\n");
        return -1;
    }
    
    // Skip to the value
    op_str = strchr(op_str, ':');
    if (!op_str) {
        printk(KERN_DEBUG MODULE_NAME ": Malformed operation field\n");
        return -1;
    }
    
    // Skip whitespace and first quote
    while (*op_str && (*op_str == ':' || *op_str == ' ' || *op_str == '"'))
        op_str++;
    
    // Now we should be at the number
    char num_str[8] = {0};  // Buffer for the number
    int i = 0;
    
    // Copy until we hit a quote or other non-digit
    while (i < 7 && op_str[i] >= '0' && op_str[i] <= '9') {
        num_str[i] = op_str[i];
        i++;
    }
    
    int code;
    if (kstrtoint(num_str, 10, &code) != 0) {
        printk(KERN_DEBUG MODULE_NAME ": Failed to parse operation code from: %s\n", num_str);
        return -1;
    }
    
    printk(KERN_DEBUG MODULE_NAME ": Successfully parsed operation code: %d\n", code);
    return code;
}

static int process_server_message(const char *buffer) {
    printk(KERN_DEBUG MODULE_NAME ": Processing message: %s\n", buffer);
    
    if (!validate_message(buffer)) {
        printk(KERN_WARNING MODULE_NAME ": Message validation failed\n");
        return 0;
    }
    
    int op = get_operation_code(buffer);
    printk(KERN_DEBUG MODULE_NAME ": Operation code: %d\n", op);
    
    switch (op) {
        case CODE_AD_BLOCK_INT:
            printk(KERN_DEBUG MODULE_NAME ": Handling ad block settings\n");
            return handle_ad_block_settings(buffer) ? 0 : -EINVAL;
            
        case CODE_ADULT_BLOCK_INT:
            printk(KERN_DEBUG MODULE_NAME ": Handling adult content settings\n");
            return handle_adult_content_settings(buffer) ? 0 : -EINVAL;
            
        case CODE_ADD_DOMAIN_INT:
            printk(KERN_DEBUG MODULE_NAME ": Handling add domain\n");
            return handle_domain_operation(buffer, true) ? 0 : -EINVAL;
            
        case CODE_REMOVE_DOMAIN_INT:
            printk(KERN_DEBUG MODULE_NAME ": Handling remove domain\n");
            return handle_domain_operation(buffer, false) ? 0 : -EINVAL;
            
        case CODE_INIT_SETTINGS_INT:
            printk(KERN_DEBUG MODULE_NAME ": Handling initial settings\n");
            return handle_initial_settings(buffer) ? 0 : -EINVAL;

        default:
            printk(KERN_WARNING MODULE_NAME ": Invalid or unhandled operation code: %d\n", op);
            return -EINVAL;
    }
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

        if (server_socket)
            printk(KERN_DEBUG MODULE_NAME ": listening...\n");
        ret = kernel_recvmsg(sock, &msg, &iov, 1, MAX_PAYLOAD - 1, 0);
        if (ret > 0) {
            buffer[ret] = '\0';
            printk(KERN_DEBUG MODULE_NAME ": Received message from server: %s\n", buffer);
            process_server_message(buffer);
        }
        else if (ret < 0) {
            printk(KERN_ERR MODULE_NAME ": Connection error: %d\n", ret);
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
        printk(KERN_ERR MODULE_NAME ": Failed to create socket\n");
        return ret;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    server_addr.sin_addr.s_addr = in_aton(SERVER_IP);

    ret = kernel_connect(server_socket, (struct sockaddr *)&server_addr, 
                        sizeof(server_addr), 0);
    if (ret < 0) {
        printk(KERN_ERR MODULE_NAME ": Failed to connect to server\n");
        sock_release(server_socket);
        return ret;
    }

    connection_thread = kthread_run(connection_handler, NULL, MODULE_NAME "_conn");
    if (IS_ERR(connection_thread)) {
        printk(KERN_ERR MODULE_NAME ": Failed to create connection thread\n");
        sock_release(server_socket);
        return PTR_ERR(connection_thread);
    }
    printk(KERN_INFO MODULE_NAME ": Network initialized\n");

    return 0;
}

void cleanup_network(void) {
    module_running = false;
    if (connection_thread)
        kthread_stop(connection_thread);
    if (server_socket)
        sock_release(server_socket);
    printk(KERN_INFO MODULE_NAME ": Network cleaned up\n");
}
