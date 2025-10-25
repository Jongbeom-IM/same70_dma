# Makefile for SAME70 USART XDMAC Project
# Converted from Microchip Studio project

# Project name
PROJECT_NAME = AS70_SAME70_XPLD_348_USART_XDMAC

# Target MCU
MCU = cortex-m7

# ARM GCC Toolchain
TOOLCHAIN_PATH = C:/gcc-arm-none-eabi/gcc-arm-none-eabi-10.3-2021.10/bin/
CC = $(TOOLCHAIN_PATH)arm-none-eabi-gcc
OBJCOPY = $(TOOLCHAIN_PATH)arm-none-eabi-objcopy
SIZE = $(TOOLCHAIN_PATH)arm-none-eabi-size
GDB = $(TOOLCHAIN_PATH)arm-none-eabi-gdb

# Directories
SRC_DIR = src
BUILD_DIR = Debug
ASF_DIR = $(SRC_DIR)/ASF

# Source files
SOURCES = \
	$(SRC_DIR)/main_usart_xdmac.c \
	$(SRC_DIR)/drv_usart_xdmac.c \
	$(SRC_DIR)/drv_usart.c \
	$(SRC_DIR)/drv_xdmac_handler.c \
	$(ASF_DIR)/common/services/clock/same70/sysclk.c \
	$(ASF_DIR)/common/services/serial/usart_serial.c \
	$(ASF_DIR)/common/utils/interrupt/interrupt_sam_nvic.c \
	$(ASF_DIR)/common/utils/stdio/read.c \
	$(ASF_DIR)/common/utils/stdio/write.c \
	$(ASF_DIR)/sam/boards/same70_xplained/init.c \
	$(ASF_DIR)/sam/drivers/mpu/mpu.c \
	$(ASF_DIR)/sam/drivers/pio/pio_handler.c \
	$(ASF_DIR)/sam/drivers/pio/pio.c \
	$(ASF_DIR)/sam/drivers/pmc/pmc.c \
	$(ASF_DIR)/sam/drivers/pmc/sleep.c \
	$(ASF_DIR)/sam/drivers/spi/spi.c \
	$(ASF_DIR)/sam/drivers/uart/uart.c \
	$(ASF_DIR)/sam/drivers/usart/usart.c \
	$(ASF_DIR)/sam/drivers/xdmac/xdmac.c \
	$(ASF_DIR)/sam/utils/cmsis/same70/source/templates/system_same70.c \
	$(ASF_DIR)/sam/utils/syscalls/gcc/syscalls.c

# ASM sources
ASM_SOURCES = \
	$(ASF_DIR)/sam/utils/cmsis/same70/source/templates/gcc/startup_same70q21.S

# Include directories
INCLUDES = \
	-I$(SRC_DIR) \
	-I$(SRC_DIR)/config \
	-I$(ASF_DIR) \
	-I$(ASF_DIR)/common/boards \
	-I$(ASF_DIR)/common/services/clock \
	-I$(ASF_DIR)/common/services/clock/same70 \
	-I$(ASF_DIR)/common/services/delay \
	-I$(ASF_DIR)/common/services/gpio \
	-I$(ASF_DIR)/common/services/ioport \
	-I$(ASF_DIR)/common/services/serial \
	-I$(ASF_DIR)/common/services/serial/sam_uart \
	-I$(ASF_DIR)/common/utils \
	-I$(ASF_DIR)/common/utils/interrupt \
	-I$(ASF_DIR)/common/utils/stdio/stdio_serial \
	-I$(ASF_DIR)/sam/boards/same70_xplained \
	-I$(ASF_DIR)/sam/drivers/mpu \
	-I$(ASF_DIR)/sam/drivers/pio \
	-I$(ASF_DIR)/sam/drivers/pmc \
	-I$(ASF_DIR)/sam/drivers/spi \
	-I$(ASF_DIR)/sam/drivers/uart \
	-I$(ASF_DIR)/sam/drivers/usart \
	-I$(ASF_DIR)/sam/drivers/xdmac \
	-I$(ASF_DIR)/sam/utils \
	-I$(ASF_DIR)/sam/utils/cmsis/same70/include \
	-I$(ASF_DIR)/sam/utils/cmsis/same70/source/templates \
	-I$(ASF_DIR)/sam/utils/header_files \
	-I$(ASF_DIR)/sam/utils/preprocessor \
	-I$(ASF_DIR)/thirdparty/CMSIS/Include

# Defines
DEFINES = \
	-D__SAME70Q21__ \
	-DBOARD=SAME70_XPLAINED \
	-DARM_MATH_CM7=true \
	-Dprintf=iprintf \
	-Dscanf=iscanf

# Compiler flags
CFLAGS = \
	-mcpu=$(MCU) \
	-mthumb \
	-mfpu=fpv5-d16 \
	-mfloat-abi=hard \
	-ffunction-sections \
	-fdata-sections \
	-mlong-calls \
	-g3 \
	-Wall \
	-Wextra \
	-Wundef \
	-Wshadow \
	-std=c99 \
	-O1 \
	$(INCLUDES) \
	$(DEFINES)

# Assembler flags
ASFLAGS = \
	-mcpu=$(MCU) \
	-mthumb \
	-mfpu=fpv5-d16 \
	-mfloat-abi=hard \
	-g3 \
	$(INCLUDES) \
	$(DEFINES)

# Linker flags
LDFLAGS = \
	-mcpu=$(MCU) \
	-mthumb \
	-mfpu=fpv5-d16 \
	-mfloat-abi=hard \
	-Wl,--start-group \
	-larm_cortexM7lfdp_math_softfp \
	-lm \
	-Wl,--end-group \
	-Wl,--gc-sections \
	-Wl,--entry=Reset_Handler \
	-Wl,--cref \
	-mlong-calls \
	-T$(ASF_DIR)/sam/utils/linker_scripts/same70/same70q21/gcc/flash.ld

# Object files
OBJECTS = $(SOURCES:%.c=$(BUILD_DIR)/%.o) $(ASM_SOURCES:%.S=$(BUILD_DIR)/%.o)

# Default target
all: $(BUILD_DIR)/$(PROJECT_NAME).elf $(BUILD_DIR)/$(PROJECT_NAME).hex $(BUILD_DIR)/$(PROJECT_NAME).bin

# Create build directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Build ELF file
$(BUILD_DIR)/$(PROJECT_NAME).elf: $(OBJECTS) | $(BUILD_DIR)
	$(CC) $(OBJECTS) $(LDFLAGS) -o $@
	$(SIZE) $@

# Build HEX file
$(BUILD_DIR)/$(PROJECT_NAME).hex: $(BUILD_DIR)/$(PROJECT_NAME).elf
	$(OBJCOPY) -O ihex $< $@

# Build BIN file
$(BUILD_DIR)/$(PROJECT_NAME).bin: $(BUILD_DIR)/$(PROJECT_NAME).elf
	$(OBJCOPY) -O binary $< $@

# Compile C source files
$(BUILD_DIR)/%.o: %.c | $(BUILD_DIR)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

# Compile ASM source files
$(BUILD_DIR)/%.o: %.S | $(BUILD_DIR)
	@mkdir -p $(dir $@)
	$(CC) $(ASFLAGS) -c $< -o $@

# Clean build files
clean:
	rm -rf $(BUILD_DIR)

# Flash using OpenOCD (requires OpenOCD and CMSIS-DAP debugger)
flash: $(BUILD_DIR)/$(PROJECT_NAME).elf
	openocd -f interface/cmsis-dap.cfg -f target/atsame70q21.cfg -c "program $(BUILD_DIR)/$(PROJECT_NAME).elf verify reset exit"

# Debug using GDB (requires OpenOCD running)
debug: $(BUILD_DIR)/$(PROJECT_NAME).elf
	$(GDB) $(BUILD_DIR)/$(PROJECT_NAME).elf

.PHONY: all clean flash debug