#include <asf.h>
#include <string.h>

#include "drv_usart.h"
#include "drv_uart_xdmac.h"
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
	uint8_t tx_buf2[34] = "USART2 - XDMAC Operation\r\n";
	uint8_t rx_buf2[10];
	uint8_t tx_buf3[34] = "UART0 - XDMAC Operation\r\n";
	uint8_t rx_buf3[10];
	uint8_t tx_buf4[34] = "UART1 - XDMAC Operation\r\n";
	uint8_t rx_buf4[10];
	uint8_t tx_buf5[34] = "UART2 - XDMAC Operation\r\n";
	uint8_t rx_buf5[10];
	uint8_t tx_buf6[34] = "UART3 - XDMAC Operation\r\n";
	uint8_t rx_buf6[10];
	uint8_t tx_buf7[34] = "UART4 - XDMAC Operation\r\n";
	uint8_t rx_buf7[10];
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

	/* Initialize USART2 with DMA */
	if(DRV_USART_Comm_Init(USART2, baudrate) != 0)
	{
		MAIN_DebugError(("Wrong USART2 Communication Interface!\r\n"));
		while(1);
	}

	/* Initialize UART0 with DMA */
	if(DRV_UART_Comm_Init(UART0, baudrate) != 0)
	{
		MAIN_DebugError(("Wrong UART0 Communication Interface!\r\n"));
		while(1);
	}

	/* Initialize UART1 with DMA */
	if(DRV_UART_Comm_Init(UART1, baudrate) != 0)
	{
		MAIN_DebugError(("Wrong UART1 Communication Interface!\r\n"));
		while(1);
	}

	/* Initialize UART2 with DMA */
	if(DRV_UART_Comm_Init(UART2, baudrate) != 0)
	{
		MAIN_DebugError(("Wrong UART2 Communication Interface!\r\n"));
		while(1);
	}


	/* Initialize UART3 with DMA */
	if(DRV_UART_Comm_Init(UART3, baudrate) != 0)
	{
		MAIN_DebugError(("Wrong UART3 Communication Interface!\r\n"));
		while(1);
	}

	/* Initialize UART4 with DMA */
	if(DRV_UART_Comm_Init(UART4, baudrate) != 0)
	{
		MAIN_DebugError(("Wrong UART4 Communication Interface!\r\n"));
		while(1);
	}

	MAIN_Debug(("USART0/USART1/USART2/UART0/UART1/UART2/UART3/UART4 initialized with XDMAC\r\n"));

	/* Insert application code here, after the board has been initialized. */

	uint32_t demo_mode = 0;  // 0 = blocking, 1 = non-blocking
	uint32_t cpu_task_counter = 0;

	while(1)
	{
		ioport_toggle_pin_level(LED_0_PIN);

		if (demo_mode == 0) {
			MAIN_Debug(("=== BLOCKING DMA MODE (Original) ===\r\n"));
			
			/* USART0 DMA operations (BLOCKING) */
			if(DRV_USART_DMA_Send(USART0, (void *)tx_buf0, sizeof(tx_buf0), 10000) == 0)
			{
				MAIN_Debug(("USART0 Send done.\r\n"));
			}

			if(DRV_USART_DMA_Recv(USART0, (void *)rx_buf0, 1, 10000) == 0)
			{
				MAIN_Debug(("Received char. from USART0 is %c\r\n", rx_buf0[0]));
			}

			/* USART1 DMA operations (BLOCKING) */
			if(DRV_USART_DMA_Send(USART1, (void *)tx_buf1, sizeof(tx_buf1), 10000) == 0)
			{
				MAIN_Debug(("USART1 Send done.\r\n"));
			}

			if(DRV_USART_DMA_Recv(USART1, (void *)rx_buf1, 1, 10000) == 0)
			{
				MAIN_Debug(("Received char. from USART1 is %c\r\n", rx_buf1[0]));
			}

			/* USART2 DMA operations (BLOCKING) */
			if(DRV_USART_DMA_Send(USART2, (void *)tx_buf2, sizeof(tx_buf2), 10000) == 0)
			{
				MAIN_Debug(("USART2 Send done.\r\n"));
			}

			if(DRV_USART_DMA_Recv(USART2, (void *)rx_buf2, 1, 10000) == 0)
			{
				MAIN_Debug(("Received char. from USART2 is %c\r\n", rx_buf2[0]));
			}

			/* UART0 DMA operations (BLOCKING) */
			if(DRV_UART_DMA_Send(UART0, (void *)tx_buf3, sizeof(tx_buf3), 10000) == 0)
			{
				MAIN_Debug(("UART0 Send done.\r\n"));
			}

			if(DRV_UART_DMA_Recv(UART0, (void *)rx_buf3, 1, 10000) == 0)
			{
				MAIN_Debug(("Received char. from UART0 is %c\r\n", rx_buf3[0]));
			}

			/* UART1 DMA operations (BLOCKING) */
			if(DRV_UART_DMA_Send(UART1, (void *)tx_buf4, sizeof(tx_buf4), 10000) == 0)
			{
				MAIN_Debug(("UART1 Send done.\r\n"));
			}

			if(DRV_UART_DMA_Recv(UART1, (void *)rx_buf4, 1, 10000) == 0)
			{
				MAIN_Debug(("Received char. from UART1 is %c\r\n", rx_buf4[0]));
			}

			/* UART2 DMA operations (BLOCKING) */
			if(DRV_UART_DMA_Send(UART2, (void *)tx_buf5, sizeof(tx_buf5), 10000) == 0)
			{
				MAIN_Debug(("UART2 Send done.\r\n"));
			}

			if(DRV_UART_DMA_Recv(UART2, (void *)rx_buf5, 1, 10000) == 0)
			{
				MAIN_Debug(("Received char. from UART2 is %c\r\n", rx_buf5[0]));
			}

			/* UART3 DMA operations (BLOCKING) */
			if(DRV_UART_DMA_Send(UART3, (void *)tx_buf6, sizeof(tx_buf6), 10000) == 0)
			{
				MAIN_Debug(("UART3 Send done.\r\n"));
			}

			if(DRV_UART_DMA_Recv(UART3, (void *)rx_buf6, 1, 10000) == 0)
			{
				MAIN_Debug(("Received char. from UART3 is %c\r\n", rx_buf6[0]));
			}

			/* UART4 DMA operations (BLOCKING) */
			if(DRV_UART_DMA_Send(UART4, (void *)tx_buf7, sizeof(tx_buf7), 10000) == 0)
			{
				MAIN_Debug(("UART4 Send done.\r\n"));
			}

			if(DRV_UART_DMA_Recv(UART4, (void *)rx_buf7, 1, 10000) == 0)
			{
				MAIN_Debug(("Received char. from UART4 is %c\r\n", rx_buf7[0]));
			}
		} 
		
		else {
			MAIN_Debug(("=== NON-BLOCKING DMA MODE (Improved) ===\r\n"));
			
			/* Start multiple DMA SEND operations concurrently */
			MAIN_Debug(("Starting concurrent DMA SEND operations...\r\n"));
			DRV_USART_DMA_Send_Start(USART0, (void *)tx_buf0, sizeof(tx_buf0));
			DRV_USART_DMA_Send_Start(USART1, (void *)tx_buf1, sizeof(tx_buf1));
			DRV_USART_DMA_Send_Start(USART2, (void *)tx_buf2, sizeof(tx_buf2));
			DRV_UART_DMA_Send_Start(UART0, (void *)tx_buf3, sizeof(tx_buf3));
			DRV_UART_DMA_Send_Start(UART1, (void *)tx_buf4, sizeof(tx_buf4));
			DRV_UART_DMA_Send_Start(UART2, (void *)tx_buf5, sizeof(tx_buf5));
			DRV_UART_DMA_Send_Start(UART3, (void *)tx_buf6, sizeof(tx_buf6));
			DRV_UART_DMA_Send_Start(UART4, (void *)tx_buf7, sizeof(tx_buf7));
			
			/* Start multiple DMA RECV operations concurrently */
			MAIN_Debug(("Starting concurrent DMA RECV operations...\r\n"));
			DRV_USART_DMA_Recv_Start(USART0, (void *)rx_buf0, 1);
			DRV_USART_DMA_Recv_Start(USART1, (void *)rx_buf1, 1);
			DRV_USART_DMA_Recv_Start(USART2, (void *)rx_buf2, 1);
			DRV_UART_DMA_Recv_Start(UART0, (void *)rx_buf3, 1);
			DRV_UART_DMA_Recv_Start(UART1, (void *)rx_buf4, 1);
			DRV_UART_DMA_Recv_Start(UART2, (void *)rx_buf5, 1);
			DRV_UART_DMA_Recv_Start(UART3, (void *)rx_buf6, 1);
			DRV_UART_DMA_Recv_Start(UART4, (void *)rx_buf7, 1);
			
			MAIN_Debug(("All DMA transfers (SEND + RECV) started - CPU is FREE!\r\n"));
			
			/* CPU can do other work while DMA operates */
			cpu_task_counter = 0;
			uint32_t send_complete_count = 0;
			uint32_t recv_complete_count = 0;
			
			while (send_complete_count < 8 || recv_complete_count < 8) {
				
				/* Check SEND completions */
				if (send_complete_count < 8) {
					uint32_t new_send_complete = 0;
					if (DRV_USART_DMA_Send_IsComplete(USART0)) new_send_complete++;
					if (DRV_USART_DMA_Send_IsComplete(USART1)) new_send_complete++;
					if (DRV_USART_DMA_Send_IsComplete(USART2)) new_send_complete++;
					if (DRV_UART_DMA_Send_IsComplete(UART0)) new_send_complete++;
					if (DRV_UART_DMA_Send_IsComplete(UART1)) new_send_complete++;
					if (DRV_UART_DMA_Send_IsComplete(UART2)) new_send_complete++;
					if (DRV_UART_DMA_Send_IsComplete(UART3)) new_send_complete++;
					if (DRV_UART_DMA_Send_IsComplete(UART4)) new_send_complete++;
					
					if (new_send_complete > send_complete_count) {
						MAIN_Debug(("SEND: %d/8 channels completed\r\n", new_send_complete));
						send_complete_count = new_send_complete;
					}
				}
				
				/* Check RECV completions */
				if (recv_complete_count < 8) {
					uint32_t new_recv_complete = 0;
					if (DRV_USART_DMA_Recv_IsComplete(USART0)) {
						new_recv_complete++;
						if (new_recv_complete > recv_complete_count) {
							MAIN_Debug(("USART0 received: %c\r\n", rx_buf0[0]));
						}
					}
					if (DRV_USART_DMA_Recv_IsComplete(USART1)) {
						new_recv_complete++;
						if (new_recv_complete > recv_complete_count) {
							MAIN_Debug(("USART1 received: %c\r\n", rx_buf1[0]));
						}
					}
					if (DRV_USART_DMA_Recv_IsComplete(USART2)) {
						new_recv_complete++;
						if (new_recv_complete > recv_complete_count) {
							MAIN_Debug(("USART2 received: %c\r\n", rx_buf2[0]));
						}
					}
					if (DRV_UART_DMA_Recv_IsComplete(UART0)) {
						new_recv_complete++;
						if (new_recv_complete > recv_complete_count) {
							MAIN_Debug(("UART0 received: %c\r\n", rx_buf3[0]));
						}
					}
					if (DRV_UART_DMA_Recv_IsComplete(UART1)) {
						new_recv_complete++;
						if (new_recv_complete > recv_complete_count) {
							MAIN_Debug(("UART1 received: %c\r\n", rx_buf4[0]));
						}
					}
					if (DRV_UART_DMA_Recv_IsComplete(UART2)) {
						new_recv_complete++;
						if (new_recv_complete > recv_complete_count) {
							MAIN_Debug(("UART2 received: %c\r\n", rx_buf5[0]));
						}
					}
					if (DRV_UART_DMA_Recv_IsComplete(UART3)) {
						new_recv_complete++;
						if (new_recv_complete > recv_complete_count) {
							MAIN_Debug(("UART3 received: %c\r\n", rx_buf6[0]));
						}
					}
					if (DRV_UART_DMA_Recv_IsComplete(UART4)) {
						new_recv_complete++;
						if (new_recv_complete > recv_complete_count) {
							MAIN_Debug(("UART4 received: %c\r\n", rx_buf7[0]));
						}
					}
					
					if (new_recv_complete > recv_complete_count) {
						MAIN_Debug(("RECV: %d/8 channels completed\r\n", new_recv_complete));
						recv_complete_count = new_recv_complete;
					}
				}
				
				/* CPU does productive work instead of waiting */
				volatile uint32_t calculation = 0;
				for (int i = 0; i < 100; i++) {
					calculation += i * i;
				}
				cpu_task_counter++;
				
				/* Add small delay to prevent timeout on receive operations */
				if (cpu_task_counter > 50000) {
					MAIN_Debug(("Timeout on some RECV operations (normal for demo)\r\n"));
					break;
				}
			}
			
			MAIN_Debug(("DMA operations complete! CPU did %d tasks meanwhile.\r\n", cpu_task_counter));
			MAIN_Debug(("SEND completed: %d/8, RECV completed: %d/8\r\n", send_complete_count, recv_complete_count));
		}

		/* Switch between blocking and non-blocking demo modes */
		demo_mode = (demo_mode + 1) % 2;
		
		if (demo_mode == 0) {
			MAIN_Debug(("Switching to BLOCKING mode next...\r\n"));
		} 
		else {
			MAIN_Debug(("Switching to NON-BLOCKING mode next...\r\n"));
		}

		/* Add some delay between demo modes */
		delay_ms(3000);
	}


	return 0;
}

/* End of File */
