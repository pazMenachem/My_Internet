#include "utils.h"

#include <linux/net.h>
#include <linux/socket.h>
#include <linux/tcp.h>
#include <net/netfilter/nf_socket.h>

static struct socket *server_socket = NULL;
static struct task_struct *connection_thread = NULL;
static bool module_running = true;

static int process_server_message(const char *buffer) {
    // Check if it's a success response
    if (!strstr(buffer, "\"code\":\"success\"")) {
        return 0;  // Ignore non-success messages
    }

    // Handle ad block settings
    if (strstr(buffer, "\"operation\":\"50\"")) {
        const char *content = strstr(buffer, "\"content\":\"");
        if (content) {
            bool enabled = strstr(content, "on") != NULL;
            update_settings(enabled, settings.adult_content_enabled);
            printk(KERN_INFO "Domain Blocker: Ad blocking %s\n", enabled ? "enabled" : "disabled");
        }
    }
    // Handle adult content block settings
    else if (strstr(buffer, "\"operation\":\"51\"")) {
        const char *content = strstr(buffer, "\"content\":\"");
        if (content) {
            bool enabled = strstr(content, "on") != NULL;
            update_settings(settings.ad_block_enabled, enabled);
            printk(KERN_INFO "Domain Blocker: Adult content blocking %s\n", enabled ? "enabled" : "disabled");
        }
    }
    // Handle add domain
    else if (strstr(buffer, "\"operation\":\"52\"")) {
        const char *content = strstr(buffer, "\"content\":\"");
        if (content) {
            content += 10;  // Skip "content":"
            const char *end = strchr(content, '"');
            if (end && (end - content) < MAX_DOMAIN_LENGTH) {
                char domain[MAX_DOMAIN_LENGTH];
                strncpy(domain, content, end - content);
                domain[end - content] = '\0';
                add_domain_to_cache(domain);
                printk(KERN_INFO "Domain Blocker: Added domain %s\n", domain);
            }
        }
    }
    // Handle remove domain
    else if (strstr(buffer, "\"operation\":\"53\"")) {
        const char *content = strstr(buffer, "\"content\":\"");
        if (content) {
            content += 10;  // Skip "content":"
            const char *end = strchr(content, '"');
            if (end && (end - content) < MAX_DOMAIN_LENGTH) {
                char domain[MAX_DOMAIN_LENGTH];
                strncpy(domain, content, end - content);
                domain[end - content] = '\0';
                remove_domain_from_cache(domain);
                printk(KERN_INFO "Domain Blocker: Removed domain %s\n", domain);
            }
        }
    }
    // Handle initial settings
    else if (strstr(buffer, "\"operation\":\"54\"")) {
        const char *content = strstr(buffer, "\"content\":");
        if (content) {
            bool ad_block = strstr(content, "\"ad_block\":\"on\"") != NULL;
            bool adult_block = strstr(content, "\"adult_block\":\"on\"") != NULL;
            update_settings(ad_block, adult_block);
            printk(KERN_INFO "Domain Blocker: Initial settings - Ad block: %s, Adult block: %s\n",
                   ad_block ? "on" : "off", adult_block ? "on" : "off");
        }
    }

    return 0;
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
        printk(KERN_ERR "Domain Blocker: Failed to create socket\n");
        return ret;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    server_addr.sin_addr.s_addr = in_aton(SERVER_IP);

    ret = kernel_connect(server_socket, (struct sockaddr *)&server_addr, 
                        sizeof(server_addr), 0);
    if (ret < 0) {
        printk(KERN_ERR "Domain Blocker: Failed to connect to server\n");
        sock_release(server_socket);
        return ret;
    }

    connection_thread = kthread_run(connection_handler, NULL, "domain_blocker_conn");
    if (IS_ERR(connection_thread)) {
        printk(KERN_ERR "Domain Blocker: Failed to create connection thread\n");
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
