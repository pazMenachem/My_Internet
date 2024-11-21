# Current directory
PWD := $(shell pwd)

debug:
	echo $(PWD)

# Module name extracted from utils.h
MODULE_NAME := $(shell grep "define MODULE_NAME" $(PWD)/src/utils.h | cut -d'"' -f2)

# Source and object files
SRC_DIR := $(PWD)/src
SRC_FILES := $(notdir $(wildcard $(SRC_DIR)/*.c))
OBJ_FILES := $(SRC_FILES:.c=.o)

# Module configuration
obj-m := $(MODULE_NAME).o
$(MODULE_NAME)-objs := $(OBJ_FILES)

# Kernel build directory
KDIR := /lib/modules/$(shell uname -r)/build

# Compiler flags
ccflags-y := -I$(SRC_DIR)

# Default target
all:
	$(MAKE) -C $(KDIR) M=$(PWD) src_dir=$(SRC_DIR) modules

# Clean build artifacts
clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
	rm -f *.o *.ko *.mod* *.symvers *.order
	rm -rf .tmp_versions

# Fix permissions if needed
permissions:
	sudo chown -R $(USER):$(USER) $(PWD)

# Module management
install:
	sudo insmod $(MODULE_NAME).ko

remove:
	sudo rmmod $(MODULE_NAME)

read:
	sudo dmesg | grep $(MODULE_NAME)

.PHONY: all clean permissions install remove read
