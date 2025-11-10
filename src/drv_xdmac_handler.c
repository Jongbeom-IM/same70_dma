/******************************************************************************
* $ Source $
*
* Workfile: drv_xdmac_handler.c
*
******************************************************************************/

#include <asf.h>

#include "drv_xdmac_handler.h"

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
			
			//printf("XDMAC Channel %d Done\r\n", channel);
		}
	}
}

/* End of File */
