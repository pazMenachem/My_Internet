# Extract module name from utils.h with simpler shell command
MODULE_NAME := $(shell grep "define MODULE_NAME" $(PWD)/src/utils.h | cut -d'"' -f2)

# Source files
obj-m := $(MODULE_NAME).o
$(MODULE_NAME)-objs := src/main.o src/cache.o src/netfilter.o src/network.o src/json_parser.o

# Kernel source directory
KDIR := /lib/modules/$(shell uname -r)/build

# Include directory
ccflags-y := -I$(src)/src

# Default target
all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
	rm -f Module.symvers Module.markers modules.order

# Install module
install:
	sudo insmod $(MODULE_NAME).ko

# Remove module
remove:
	sudo rmmod $(MODULE_NAME)

read:
	sudo dmesg | grep $(MODULE_NAME)

.PHONY: all clean install remove read