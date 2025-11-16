/******************************************************************************
* $ Source $
*
* Workfile: drv_usart.c
*
******************************************************************************/

#include <asf.h>

#include "drv_usart.h"


/******************************************************************************
* USART Configuration Structure
******************************************************************************/
typedef struct {
	Usart *usart;
	uint32_t peripheral_id;
	uint32_t rxd_gpio;
	uint32_t rxd_flags;
	uint32_t txd_gpio;
	uint32_t txd_flags;
} usart_config_t;

typedef struct {
	Uart *uart;
	uint32_t peripheral_id;
	uint32_t rxd_gpio;
	uint32_t rxd_flags;
	uint32_t txd_gpio;
	uint32_t txd_flags;
} uart_config_t;

/* USART Configuration Table */
static const usart_config_t usart_configs[] = {
	{
		.usart = USART0,
		.peripheral_id = ID_USART0,
		.rxd_gpio = USART0_RXD_GPIO,
		.rxd_flags = USART0_RXD_FLAGS,
		.txd_gpio = USART0_TXD_GPIO,
		.txd_flags = USART0_TXD_FLAGS
	},
	{
		.usart = USART1,
		.peripheral_id = ID_USART1,
		.rxd_gpio = USART1_RXD_GPIO,
		.rxd_flags = USART1_RXD_FLAGS,
		.txd_gpio = USART1_TXD_GPIO,
		.txd_flags = USART1_TXD_FLAGS
	},
	{
		.usart = USART2,
		.peripheral_id = ID_USART2,
		.rxd_gpio = USART2_RXD_GPIO,
		.rxd_flags = USART2_RXD_FLAGS,
		.txd_gpio = USART2_TXD_GPIO,
		.txd_flags = USART2_TXD_FLAGS
	}
};

static const uart_config_t uart_configs[] = {
	{
		.uart = UART0,
		.peripheral_id = ID_UART0,
		.rxd_gpio = UART0_RXD_GPIO,
		.rxd_flags = UART0_RXD_FLAGS,
		.txd_gpio = UART0_TXD_GPIO,
		.txd_flags = UART0_TXD_FLAGS
	},
	{
		.uart = UART1,
		.peripheral_id = ID_UART1,
		.rxd_gpio = UART1_RXD_GPIO,
		.rxd_flags = UART1_RXD_FLAGS,
		.txd_gpio = UART1_TXD_GPIO,
		.txd_flags = UART1_TXD_FLAGS
	},
	{
		.uart = UART2,
		.peripheral_id = ID_UART2,
		.rxd_gpio = UART2_RXD_GPIO,
		.rxd_flags = UART2_RXD_FLAGS,
		.txd_gpio = UART2_TXD_GPIO,
		.txd_flags = UART2_TXD_FLAGS
	},
	{
		.uart = UART3,
		.peripheral_id = ID_UART3,
		.rxd_gpio = UART3_RXD_GPIO,
		.rxd_flags = UART3_RXD_FLAGS,
		.txd_gpio = UART3_TXD_GPIO,
		.txd_flags = UART3_TXD_FLAGS
	},
	{
		.uart = UART4,
		.peripheral_id = ID_UART4,
		.rxd_gpio = UART4_RXD_GPIO,
		.rxd_flags = UART4_RXD_FLAGS,
		.txd_gpio = UART4_TXD_GPIO,
		.txd_flags = UART4_TXD_FLAGS

	}
};

#define USART_CONFIG_COUNT (sizeof(usart_configs) / sizeof(usart_configs[0]))
#define UART_CONFIG_COUNT (sizeof(uart_configs) / sizeof(uart_configs[0]))

/* Helper function to get USART configuration */
static const usart_config_t* get_usart_config(Usart *pusart)
{
	for (uint32_t i = 0; i < USART_CONFIG_COUNT; i++) {
		if (usart_configs[i].usart == pusart) {
			return &usart_configs[i];
		}
	}
	return NULL;
}

/* Helper function to get UART configuration */
static const uart_config_t* get_uart_config(Uart *puart)
{
	for (uint32_t i = 0; i < UART_CONFIG_COUNT; i++) {
		if (uart_configs[i].uart == puart) {
			return &uart_configs[i];
		}
	}
	return NULL;
}


#ifdef DEBUG
#include <stdio.h>

#define USART_Debug(x)					//printf x
#define USART_DebugError(x)				//printf x
#else
#define USART_Debug(x)
#define USART_DebugError(x)
#endif




/*********************************************************************
*	Function	: DRV_USART_Comm_Init()
*	Description : This function initialize USART0 for F/W downloading.
*	Argument	:
*	Return		:
*********************************************************************/

uint32_t DRV_USART_Comm_Init(Usart *pusart, uint32_t baudrate)
{
	const usart_config_t *config;
	sam_usart_opt_t usart_settings = {
		.baudrate = baudrate,
		.char_length = US_MR_CHRL_8_BIT,
		.parity_type = US_MR_PAR_NO,
		.stop_bits = US_MR_NBSTOP_1_BIT,
		.channel_mode = US_MR_CHMODE_NORMAL,
	};

	/* Get USART configuration */
	config = get_usart_config(pusart);
	if (config == NULL) {
		USART_DebugError(("Unsupported USART instance\r\n"));
		return 1;
	}

	/* Enable peripheral clock and configure pins dynamically */
	pmc_enable_periph_clk(config->peripheral_id);
	ioport_set_pin_mode(config->rxd_gpio, config->rxd_flags);
	ioport_disable_pin(config->rxd_gpio);
	ioport_set_pin_mode(config->txd_gpio, config->txd_flags);
	ioport_disable_pin(config->txd_gpio);

	/* Configure USART */
	usart_reset(pusart);
	usart_init_rs232(pusart, &usart_settings, sysclk_get_peripheral_hz());

	/* Flush RHR */
	(void)(pusart->US_RHR);

	usart_enable_tx(pusart);
	usart_enable_rx(pusart);

	USART_Debug(("USART (0x%08x) initialized successfully\r\n", (uint32_t)pusart));

	return 0;
}


uint32_t DRV_UART_Comm_Init(Uart *puart, uint32_t baudrate)
{
	const uart_config_t *config;
	sam_uart_opt_t uart_settings = {
		.ul_mck = sysclk_get_peripheral_hz(),
		.ul_baudrate = baudrate,
		.ul_mode = UART_MR_PAR_NO
	};

	/* Get UART configuration */
	config = get_uart_config(puart);
	if (config == NULL) {
		USART_DebugError(("Unsupported UART instance\r\n"));
		return 1;
	}

	/* Enable peripheral clock and configure pins dynamically */
	pmc_enable_periph_clk(config->peripheral_id);
	ioport_set_pin_mode(config->rxd_gpio, config->rxd_flags);
	ioport_disable_pin(config->rxd_gpio);
	ioport_set_pin_mode(config->txd_gpio, config->txd_flags);
	ioport_disable_pin(config->txd_gpio);

	/* Configure UART */
	uart_reset(puart);
	uart_init(puart, &uart_settings);

	/* Enable UART TX and RX */
	uart_enable_tx(puart);
	uart_enable_rx(puart);

	USART_Debug(("UART (0x%08x) initialized successfully\r\n", (uint32_t)puart));

	return 0;
}




/*********************************************************************
*	Function	: DRV_USART_Comm_Fin()
*	Description : Finalize USART to download F/W
*	Argument	:
*	Return		:
*********************************************************************/

uint32_t DRV_USART_Comm_Fin(Usart *pusart)
{
	usart_disable_tx(pusart);
	usart_disable_rx(pusart);


	return 0;
}

uint32_t DRV_UART_Comm_Fin(Uart *puart)
{
	uart_disable_tx(puart);
	uart_disable_rx(puart);

	
	return 0;
}

/* End of File */
