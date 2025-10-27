# PowerShell Build Script for SAME70 Project
# Replaces GNU Make functionality

param(
    [string]$Target = "all"
)

# Configuration
$ProjectName = "AS70_SAME70_XPLD_348_USART_XDMAC"
$BuildDir = "Debug"
$SrcDir = "src"
$ASFDir = "$SrcDir/ASF"

# Toolchain paths (Using Atmel Studio toolchain)
$ToolchainPath = "C:/Program Files (x86)/Atmel/Studio/7.0/toolchain/arm/arm-gnu-toolchain/bin/"
$CC = "${ToolchainPath}arm-none-eabi-gcc.exe"
$OBJCOPY = "${ToolchainPath}arm-none-eabi-objcopy.exe"
$SIZE = "${ToolchainPath}arm-none-eabi-size.exe"

# Compiler flags
$CFLAGS = @(
    "-mcpu=cortex-m7",
    "-mthumb",
    "-mfpu=fpv5-d16",
    "-mfloat-abi=hard",
    "-ffunction-sections",
    "-fdata-sections",
    "-mlong-calls",
    "-g3",
    "-Wall",
    "-Wextra",
    "-Wundef",
    "-Wshadow",
    "-std=c99",
    "-O1"
)

# Include directories
$INCLUDES = @(
    "-I$SrcDir",
    "-I$SrcDir/config",
    "-I$ASFDir",
    "-I$ASFDir/common/boards",
    "-I$ASFDir/common/services/clock",
    "-I$ASFDir/common/services/clock/same70",
    "-I$ASFDir/common/services/delay",
    "-I$ASFDir/common/services/gpio",
    "-I$ASFDir/common/services/ioport",
    "-I$ASFDir/common/services/serial",
    "-I$ASFDir/common/services/serial/sam_uart",
    "-I$ASFDir/common/utils",
    "-I$ASFDir/common/utils/interrupt",
    "-I$ASFDir/common/utils/stdio/stdio_serial",
    "-I$ASFDir/sam/boards",
    "-I$ASFDir/sam/boards/same70_xplained",
    "-I$ASFDir/sam/drivers/mpu",
    "-I$ASFDir/sam/drivers/pio",
    "-I$ASFDir/sam/drivers/pmc",
    "-I$ASFDir/sam/drivers/spi",
    "-I$ASFDir/sam/drivers/uart",
    "-I$ASFDir/sam/drivers/usart",
    "-I$ASFDir/sam/drivers/xdmac",
    "-I$ASFDir/sam/utils",
    "-I$ASFDir/sam/utils/cmsis/same70/include",
    "-I$ASFDir/sam/utils/cmsis/same70/source/templates",
    "-I$ASFDir/sam/utils/header_files",
    "-I$ASFDir/sam/utils/preprocessor",
    "-I$ASFDir/sam/utils/fpu",
    "-I$ASFDir/thirdparty/CMSIS/Include"
)

# Defines
$DEFINES = @(
    "-D__SAME70Q21__",
    "-DBOARD=SAME70_XPLAINED",
    "-DARM_MATH_CM7=true",
    "-Dprintf=iprintf",
    "-Dscanf=iscanf"
)

# Source files
$SOURCES = @(
    "$SrcDir/main_usart_xdmac.c",
    "$SrcDir/drv_usart_xdmac.c",
    "$SrcDir/drv_usart.c",
    "$SrcDir/drv_xdmac_handler.c",
    "$ASFDir/common/services/clock/same70/sysclk.c",
    "$ASFDir/common/services/serial/usart_serial.c",
    "$ASFDir/common/utils/interrupt/interrupt_sam_nvic.c",
    "$ASFDir/common/utils/stdio/read.c",
    "$ASFDir/common/utils/stdio/write.c",
    "$ASFDir/sam/boards/same70_xplained/init.c",
    "$ASFDir/sam/drivers/mpu/mpu.c",
    "$ASFDir/sam/drivers/pio/pio_handler.c",
    "$ASFDir/sam/drivers/pio/pio.c",
    "$ASFDir/sam/drivers/pmc/pmc.c",
    "$ASFDir/sam/drivers/pmc/sleep.c",
    "$ASFDir/sam/drivers/spi/spi.c",
    "$ASFDir/sam/drivers/uart/uart.c",
    "$ASFDir/sam/drivers/usart/usart.c",
    "$ASFDir/sam/drivers/xdmac/xdmac.c",
    "$ASFDir/sam/utils/cmsis/same70/source/templates/system_same70.c",
    "$ASFDir/sam/utils/syscalls/gcc/syscalls.c"
)

# ASM sources
$ASM_SOURCES = @(
    "$ASFDir/sam/utils/cmsis/same70/source/templates/gcc/startup_same70q21.S"
)

# Linker flags
$LDFLAGS = @(
    "-mcpu=cortex-m7",
    "-mthumb",
    "-mfpu=fpv5-d16",
    "-mfloat-abi=hard",
    "-Wl,--start-group",
    "-lm",
    "-Wl,--end-group",
    "-Wl,--gc-sections",
    "-Wl,--entry=Reset_Handler",
    "-Wl,--cref",
    "-mlong-calls",
    "-T$ASFDir/sam/utils/linker_scripts/same70/same70q21/gcc/flash.ld"
)

function Build-Project {
    Write-Host "Building SAME70 Project..." -ForegroundColor Green
    
    # Create build directory
    if (!(Test-Path $BuildDir)) {
        New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
    }
    
    # Compile C sources
    $objects = @()
    foreach ($source in $SOURCES) {
        if (Test-Path $source) {
            $objName = [System.IO.Path]::GetFileNameWithoutExtension($source) + ".o"
            $objPath = "$BuildDir/$objName"
            $objects += $objPath
            
            Write-Host "Compiling: $source" -ForegroundColor Cyan
            $compileArgs = $CFLAGS + $INCLUDES + $DEFINES + @("-c", $source, "-o", $objPath)
            & $CC $compileArgs
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Compilation failed for $source" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "Source file not found: $source" -ForegroundColor Yellow
        }
    }
    
    # Compile ASM sources
    foreach ($source in $ASM_SOURCES) {
        if (Test-Path $source) {
            $objName = [System.IO.Path]::GetFileNameWithoutExtension($source) + ".o"
            $objPath = "$BuildDir/$objName"
            $objects += $objPath
            
            Write-Host "Assembling: $source" -ForegroundColor Cyan
            $asmArgs = $CFLAGS + $INCLUDES + $DEFINES + @("-c", $source, "-o", $objPath)
            & $CC $asmArgs
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Assembly failed for $source" -ForegroundColor Red
                exit 1
            }
        }
    }
    
    # Link
    $elfFile = "$BuildDir/$ProjectName.elf"
    Write-Host "Linking: $elfFile" -ForegroundColor Magenta
    $linkArgs = $objects + $LDFLAGS + @("-o", $elfFile)
    & $CC $linkArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Linking failed" -ForegroundColor Red
        exit 1
    }
    
    # Show size
    Write-Host "Size information:" -ForegroundColor Green
    & $SIZE $elfFile
    
    # Generate HEX file
    $hexFile = "$BuildDir/$ProjectName.hex"
    Write-Host "Generating HEX: $hexFile" -ForegroundColor Green
    & $OBJCOPY "-O" "ihex" $elfFile $hexFile
    
    # Generate BIN file
    $binFile = "$BuildDir/$ProjectName.bin"
    Write-Host "Generating BIN: $binFile" -ForegroundColor Green
    & $OBJCOPY "-O" "binary" $elfFile $binFile
    
    Write-Host "Build completed successfully!" -ForegroundColor Green
}

function Clean-Project {
    Write-Host "Cleaning build directory..." -ForegroundColor Yellow
    if (Test-Path $BuildDir) {
        Remove-Item -Path $BuildDir -Recurse -Force
    }
    Write-Host "Clean completed!" -ForegroundColor Green
}

# Main execution
switch ($Target) {
    "clean" { Clean-Project }
    "all" { Build-Project }
    default { Build-Project }
}