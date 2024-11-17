// network.c
#include "domain_blocker.h"

static struct socket *client_socket = NULL;
static struct task_struct *connection_thread = NULL;
static bool module_running = true;

static int send_sync_request(struct socket *sock) {
    char *json_msg;
    int msg_len;
    struct msghdr msg;
    struct kvec iov;
    int ret;

    json_msg = kmalloc(MAX_PAYLOAD, GFP_KERNEL);
    if (!json_msg)
        return -ENOMEM;

    msg_len = snprintf(json_msg, MAX_PAYLOAD,
                      "{\"code\":\"55\",\"content\":\"sync\"}\n");

    memset(&msg, 0, sizeof(msg));
    iov.iov_base = json_msg;
    iov.iov_len = msg_len;

    ret = kernel_sendmsg(sock, &msg, &iov, 1, msg_len);
    kfree(json_msg);

    return ret;
}

static int process_server_message(const char *buffer) {
    if (strstr(buffer, "\"operation\":\"55\"")) {
        bool ad_block = strstr(buffer, "\"ad_block\":\"on\"") != NULL;
        bool adult_block = strstr(buffer, "\"adult_block\":\"on\"") != NULL;
        update_settings(ad_block, adult_block);
    }
    return 0;
}

static int receive_server_updates(struct socket *sock) {
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
            buffer[ret