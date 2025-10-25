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
	uint32_t channel_status;
	uint32_t channel;
	
	/* Check all 24 channels dynamically */
	for (channel = 0; channel < 24; channel++) {
		channel_status = XDMAC->XDMAC_CHID[channel].XDMAC_CIS;
		
		if (channel_status & XDMAC_CIS_BIS) {
			/* Set channel-specific completion flag */
			g_xdmac_channel_done[channel] = 1;
			
			/* Maintain backward compatibility with legacy flags */
			/* Check if this is a TX or RX channel we're using */
			if (channel == 1 || channel == 3) { /* TX channels */
				g_xdmac_tx_done = 1;
			}
			if (channel == 2 || channel == 4) { /* RX channels */
				g_xdmac_rx_done = 1;
			}
			
			//printf("XDMAC Channel %d Done\r\n", channel);
		}
	}
}

/* End of File */
