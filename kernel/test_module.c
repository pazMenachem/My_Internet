#include <sys/socket.h>
#include <linux/netlink.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>

#define NETLINK_USER 31
#define MAX_PAYLOAD 1024

struct server_msg {
    char code[32];
    char content[MAX_PAYLOAD];
};

int main()
{
    struct sockaddr_nl src_addr, dest_addr;
    struct nlmsghdr *nlh = NULL;
    struct server_msg msg;
    struct iovec iov;
    struct msghdr message;
    int sock_fd;

    // Create socket
    sock_fd = socket(PF_NETLINK, SOCK_RAW, NETLINK_USER);
    if (sock_fd < 0) {
        perror("Socket creation failed");
        return -1;
    }

    // Initialize source address
    memset(&src_addr, 0, sizeof(src_addr));
    src_addr.nl_family = AF_NETLINK;
    src_addr.nl_pid = getpid();

    // Bind socket
    bind(sock_fd, (struct sockaddr *)&src_addr, sizeof(src_addr));

    // Initialize destination address
    memset(&dest_addr, 0, sizeof(dest_addr));
    dest_addr.nl_family = AF_NETLINK;
    dest_addr.nl_pid = 0; // For kernel
    dest_addr.nl_groups = 0; // Unicast

    // Prepare message
    nlh = (struct nlmsghdr *)malloc(NLMSG_SPACE(sizeof(struct server_msg)));
    memset(nlh, 0, NLMSG_SPACE(sizeof(struct server_msg)));
    nlh->nlmsg_len = NLMSG_SPACE(sizeof(struct server_msg));
    nlh->nlmsg_pid = getpid();
    nlh->nlmsg_flags = 0;

    // Fill the message
    struct server_msg *payload = (struct server_msg *)NLMSG_DATA(nlh);
    strcpy(payload->code, "100");
    strcpy(payload->content, "Hello from userspace!");

    iov.iov_base = (void *)nlh;
    iov.iov_len = nlh->nlmsg_len;
    message.msg_name = (void *)&dest_addr;
    message.msg_namelen = sizeof(dest_addr);
    message.msg_iov = &iov;
    message.msg_iovlen = 1;

    // Send message
    sendmsg(sock_fd, &message, 0);
    printf("Message sent to kernel\n");

    // Receive response
    recvmsg(sock_fd, &message, 0);
    struct server_msg *received_msg = (struct server_msg *)NLMSG_DATA(nlh);
    printf("Received from kernel: code=%s, content=%s\n", 
           received_msg->code, received_msg->content);

    close(sock_fd);
    return 0;
} 