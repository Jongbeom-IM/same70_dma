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
	}
};

#define USART_CONFIG_COUNT (sizeof(usart_configs) / sizeof(usart_configs[0]))

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

/* End of File */
