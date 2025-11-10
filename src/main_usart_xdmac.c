#include <asf.h>
#include <string.h>

#include "drv_usart.h"
#include "drv_usart_xdmac.h"


/******************************************************************************
 *  DEBUG MACRO
 *****************************************************************************/

#ifdef DEBUG
#include <stdio.h>

#define MAIN_Debug(x)					printf x
#define MAIN_TxtInfo(x)					printf x
#define MAIN_DebugError(x)				printf x
#else
#define MAIN_Debug(x)
#define MAIN_TxtInfo(x)
#define MAIN_DebugError(x)
#endif


/******************************************************************************
 *  Global/Static Variables
 *****************************************************************************/

/* Communication instance - currently unused */
// static void *sp_drv_instance = NULL;




/*********************************************************************
*	Function	: configure_console()
*	Description : This initialize UART port for virtual COM-port.
*	Argument	:
*	Return		:
*********************************************************************/

static void configure_console(void)
{
	const usart_serial_options_t usart_serial_options = {
		.baudrate = 115200,
		.charlength = US_MR_CHRL_8_BIT,
		.paritytype = US_MR_PAR_NO,
		.stopbits = US_MR_NBSTOP_1_BIT,
	};

	/* Configure console UART. */
	sysclk_enable_peripheral_clock(CONSOLE_UART_ID);
	stdio_serial_init(CONSOLE_UART, &usart_serial_options);
}




/*********************************************************************
*	Function	: main()
*	Description :
*	Argument	:
*	Return		:
*********************************************************************/

int main(void)
{
	uint8_t tx_buf0[34] = "USART0 - XDMAC Operation\r\n";
	uint8_t rx_buf0[10];
	uint8_t tx_buf1[34] = "USART1 - XDMAC Operation\r\n";
	uint8_t rx_buf1[10];
	uint32_t baudrate;


	/* Initialize system clock */
	sysclk_init();

	/* Initialize basic board I/O */
	board_init();


	/* Configure EDBG USART */
	configure_console();

	MAIN_Debug(("===============================================\r\n"));
	MAIN_Debug(("[SAME70 XPLD - USART XDMAC Test\r\n"));
	MAIN_Debug(("===============================================\r\n"));
	MAIN_Debug(("Processor Clock = %d Hz\r\n", sysclk_get_cpu_hz()));

	pmc_enable_periph_clk(ID_XDMAC);

	baudrate = 115200;

	/* Initialize USART0 with DMA */
	if(DRV_USART_Comm_Init(USART0, baudrate) != 0)
	{
		MAIN_DebugError(("Wrong USART0 Communication Interface!\r\n"));
		while(1);
	}

	/* Initialize USART1 with DMA */
	if(DRV_USART_Comm_Init(USART1, baudrate) != 0)
	{
		MAIN_DebugError(("Wrong USART1 Communication Interface!\r\n"));
		while(1);
	}

	MAIN_Debug(("USART0 and USART1 initialized with XDMAC\r\n"));

	/* Insert application code here, after the board has been initialized. */

	while(1)
	{
		ioport_toggle_pin_level(LED_0_PIN);

		/* USART0 DMA operations */
		if(DRV_USART_DMA_Send(USART0, (void *)tx_buf0, sizeof(tx_buf0), 10000) == 0)
		{
			MAIN_Debug(("USART0 Send done.\r\n"));
		}

		if(DRV_USART_DMA_Recv(USART0, (void *)rx_buf0, 1, 100000) == 0)
		{
			MAIN_Debug(("Received char. from USART0 is %c\r\n", rx_buf0[0]));
		}

		/* USART1 DMA operations */
		if(DRV_USART_DMA_Send(USART1, (void *)tx_buf1, sizeof(tx_buf1), 10000) == 0)
		{
			MAIN_Debug(("USART1 Send done.\r\n"));
		}

		if(DRV_USART_DMA_Recv(USART1, (void *)rx_buf1, 1, 100000) == 0)
		{
			MAIN_Debug(("Received char. from USART1 is %c\r\n", rx_buf1[0]));
		}

		/* Add some delay between operations */
		delay_ms(1000);
	}


	return 0;
}

/* End of File */
