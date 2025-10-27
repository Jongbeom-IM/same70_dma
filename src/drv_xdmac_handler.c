/******************************************************************************
* $ Source $
*
* Workfile: drv_xdmac_handler.c
*
******************************************************************************/

#include <asf.h>

#include "drv_xdmac_handler.h"


/* Global DMA completion flags for each channel */
volatile uint8_t g_xdmac_tx_done = 0, g_xdmac_rx_done = 0;

/* Channel-specific completion flags */
volatile uint8_t g_xdmac_channel_done[24] = {0}; /* SAME70 has 24 DMA channels */




/**
 * \brief XDMAC interrupt handler for all channels.
 */
void XDMAC_Handler(void)
{
	uint32_t global_status;
	uint32_t channel;
	uint32_t channel_status;
	
	/* Read global interrupt status - only active channels will have bits set */
	global_status = XDMAC->XDMAC_GIS;
	
	/* Process only channels that have interrupts pending */
	while (global_status) {
		/* Find the first set bit (lowest channel number with interrupt) */
		channel = __builtin_ctz(global_status);  // Count trailing zeros - GCC builtin
		
		/* Clear the bit for this channel in our local copy */
		global_status &= ~(1UL << channel);
		
		/* Read and clear channel-specific interrupt status */
		channel_status = XDMAC->XDMAC_CHID[channel].XDMAC_CIS;
		
		if (channel_status & XDMAC_CIS_BIS) {
			/* Set channel-specific completion flag */
			g_xdmac_channel_done[channel] = 1;
			
			/* Maintain backward compatibility with legacy flags */
			/* Map channels to legacy TX/RX flags based on actual usage */
			switch (channel) {
				case XDMAC_USART0_TX_CH:
				case XDMAC_USART1_TX_CH:
				case XDMAC_USART2_TX_CH:
				case XDMAC_UART0_TX_CH:
				case XDMAC_UART1_TX_CH:
				case XDMAC_UART2_TX_CH:
				case XDMAC_UART3_TX_CH:
				case XDMAC_UART4_TX_CH:
					g_xdmac_tx_done = 1;
					break;
					
				case XDMAC_USART0_RX_CH:
				case XDMAC_USART1_RX_CH:
				case XDMAC_USART2_RX_CH:
				case XDMAC_UART0_RX_CH:
				case XDMAC_UART1_RX_CH:
				case XDMAC_UART2_RX_CH:
				case XDMAC_UART3_RX_CH:
				case XDMAC_UART4_RX_CH:
					g_xdmac_rx_done = 1;
					break;
					
				default:
					/* Other peripherals - no legacy flag update needed */
					break;
			}
			
			//printf("XDMAC Channel %d Done\r\n", channel);
		}
	}
}

/* End of File */
