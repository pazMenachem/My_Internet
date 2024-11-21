#include <linux/errno.h>
#include <linux/string.h>
#include <linux/kernel.h>  
#include <linux/printk.h>
#include <linux/module.h>
#include "utils.h"

/**
 * get_json_value - Extract value for a given key from JSON string
 * @buffer: Input JSON string
 * @key: Key to search for (max 124 chars)
 * @value_start: Pointer to store the start position of the value
 * @value_len: Pointer to store the length of the value
 *
 * Return: 0 on success, negative on failure
 *         -EINVAL: Invalid input parameters or malformed JSON
 *         -ENOENT: Key not found
 *         -EOVERFLOW: Key too long
 */
int get_json_value(const char *buffer, const char *key, const char **value_start, size_t *value_len);

/**
 * get_operation_code - Extract operation code from JSON string
 * @buffer: Input JSON string
 *
 * Return: Operation code on success, negative on failure
 *         -EINVAL: Invalid input parameters or malformed JSON
 *         -ENOENT: Operation code not found
 */
int get_operation_code(const char *buffer);

/**
 * parse_settings - Parse settings from JSON string
 * @buffer: Input JSON string
 * @value_start: Pointer to store the start position of the value
 * @value_len: Pointer to store the length of the value
 * @example: 
 * {
 *     "settings": {
 *         "key1": "value1",
 *         "key2": "value2"
 *     }w
 * }
 *
 * Return: 0 on success, negative on failure
 */
int parse_settings(const char *buffer, const char **value_start, size_t *value_len);
