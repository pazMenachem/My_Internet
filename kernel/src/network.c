#include "network.h"

/* Private definitions */
static struct socket *server_socket = NULL;
static struct task_struct *connection_thread = NULL;
static bool module_running = true;

/**
 * validate_message - Validates server response contains success code
 * @buffer: Null-terminated string containing JSON message
 *
 * Return: true if message contains success code, false otherwise
 */
static bool validate_message(const char *buffer) {    
    char code_pattern[32];
    snprintf(code_pattern, sizeof(code_pattern), "\"%s\"", CODE_SUCCESS);
    
    const char *code_pos = strstr(buffer, code_pattern);
    bool valid = (code_pos != NULL);
    
    if (!valid)
        printk(KERN_DEBUG MODULE_NAME ": Message validation result: Message is invalid\n");
    
    return valid;
}

/**
 * handle_domain_operation - Process domain addition/removal requests
 * @buffer: Null-terminated string containing JSON message
 * @is_add: true for domain addition, false for removal
 *
 * Extracts domain from JSON message and performs requested cache operation
 *
 * Return: true on success, false on failure
 */
static bool handle_domain_operation(const char *buffer, bool is_add) {
    const char *value_start;
    size_t value_len;
    int ret = get_json_value(buffer, STR_CONTENT, &value_start, &value_len);
    
    if (ret < 0) {
        printk(KERN_WARNING MODULE_NAME ": Failed to get domain content: %d\n", ret);
        return false;
    }
    
    if (value_len >= MAX_DOMAIN_LENGTH) {
        printk(KERN_WARNING MODULE_NAME ": Domain too long\n");
        return false;
    }
    
    char domain[MAX_DOMAIN_LENGTH];
    memcpy(domain, value_start, value_len);
    domain[value_len] = '\0';
    
    if (is_add)
        add_domain_to_cache(domain);
     else 
        remove_domain_from_cache(domain);

    return true;
}

/**
 * handle_initial_settings - Process initial settings message
 * @buffer: Null-terminated string containing JSON message
 *
 * Parses initial domain list and settings from server
 *
 * Return: true on success, false on failure
 */
static bool handle_initial_settings(const char *buffer) {
    int ret = 0;
    ret = parse_domains(buffer);
    if (ret < 0) {
        printk(KERN_WARNING MODULE_NAME ": Failed to parse domains: %d\n", ret);
        return false;
    }

    printk(KERN_INFO MODULE_NAME ": Successfully initialized settings and domains\n");
    return true;
}

/**
 * process_server_message - Process incoming JSON messages from server
 * @buffer: Null-terminated string containing JSON message
 *
 * Validates message and routes to appropriate handler based on operation code:
 * - CODE_ADD_DOMAIN_INT: Add domain to cache
 * - CODE_REMOVE_DOMAIN_INT: Remove domain from cache
 * - CODE_INIT_SETTINGS_INT: Initialize domain list
 *
 * Return: 0 on success, -EINVAL on validation or processing failure
 */
static int process_server_message(const char *buffer) {
    
    if (!validate_message(buffer)) {
        printk(KERN_WARNING MODULE_NAME ": Message validation failed\n");
        return 0;
    }
    
    switch (get_operation_code(buffer)) {
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
            printk(KERN_WARNING MODULE_NAME ": Invalid or unhandled operation code\n");
            return -EINVAL;
    }
}

/**
 * connection_handler - Kernel thread for handling server communication
 * @data: Thread data (unused)
 *
 * Continuously listens for messages from server and processes them
 * until module_running is set to false
 *
 * Return: 0 on normal exit, -ENOMEM on memory allocation failure
 */
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
            printk(KERN_DEBUG MODULE_NAME ": Listening...\n");
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
