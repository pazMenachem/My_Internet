#include "json_parser.h"

int get_json_value(const char *buffer, const char *key, 
                   const char **value_start, size_t *value_len)
{
    if (!buffer || !key)
        return -EINVAL;

    if (strlen(key) > 124)  // 128 - 3 (quotes + null) - 1 (safety)
        return -EOVERFLOW;

    char key_pattern[128];
    const char *start, *end;
    
    snprintf(key_pattern, sizeof(key_pattern), "\"%s\"", key);
    
    start = strstr(buffer, key_pattern);
    if (!start)
        return -ENOENT;
    
    start += strlen(key_pattern) + 2;  // +1 for colon and space
    
    switch (*start) {
    case '"':
        start++;
        end = strchr(start + 1, '"');
        break;
    case '[':
        end = strchr(start + 1, ']');
        end++;
        break;
    default:
        return -EINVAL;
    }
    
    if (!end)
        return -EINVAL;
    
    *value_start = start;
    *value_len = (*start != '"') ? end - start : end - start + 1;
    
    return 0;
}

int get_operation_code(const char *buffer) {    
    const char *value_start;
    size_t value_len;
    int ret = get_json_value(buffer, STR_OPERATION, &value_start, &value_len);
    
    if (ret < 0) {
        printk(KERN_WARNING MODULE_NAME ": Failed to find operation field: %d\n", ret);
        return ENOENT;
    }
    
    char num_str[8] = {0};
    if (value_len >= sizeof(num_str)) {
        printk(KERN_WARNING MODULE_NAME ": Operation code too long\n");
        return EINVAL;
    }
    
    strncpy(num_str, value_start, value_len);
    
    int code;
    if (kstrtoint(num_str, 10, &code) != 0) {
        printk(KERN_WARNING MODULE_NAME ": Failed to parse operation code from: %s\n", num_str);
        return EINVAL;
    }
    return code;
}
