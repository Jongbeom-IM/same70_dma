/******************************************************************************
* $ Source $
*
* Workfile: drv_xdmac_handler.c
*
******************************************************************************/

#include <asf.h>

#include "drv_xdmac_handler.h"


volatile uint8_t g_xdmac_tx_done = 0, g_xdmac_rx_done = 0;




/**
 * \brief XDMAC interrupt handler.
 */
void XDMAC_Handler(void)
{
	if(XDMAC->XDMAC_CHID[XDMAC_TX_CH].XDMAC_CIS & XDMAC_CIS_BIS)
	{
		//printf("TX\r\n");
		g_xdmac_tx_done = 1;
	}

	if(XDMAC->XDMAC_CHID[XDMAC_RX_CH].XDMAC_CIS & XDMAC_CIS_BIS)
	{
		//printf("RX\r\n");
		g_xdmac_rx_done = 1;
	}
}

/* End of File */
