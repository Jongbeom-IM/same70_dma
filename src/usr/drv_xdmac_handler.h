#ifndef __DRV_SAM_S70_E70_V71_XDMAC_HANDLER_H__
#define __DRV_SAM_S70_E70_V71_XDMAC_HANDLER_H__


/******************************************************************************
* include
******************************************************************************/


/******************************************************************************
* MACRO
******************************************************************************/

/** Physical XDMAC channel used in this example. */
#define XDMAC_TX_CH						1
#define XDMAC_RX_CH						2

/** XDMAC channel HW Interface number for SPI0, refer to datasheet. */
#define SPI0_XDMAC_TX_CH_NUM			1
#define SPI0_XDMAC_RX_CH_NUM			2

/** XDMAC for peripheral connection number for USART0, refer to datasheet. */
#define USART0_XDMAC_TX_CH_NUM			7
#define USART0_XDMAC_RX_CH_NUM			8


/******************************************************************************
* Variables
******************************************************************************/

extern volatile uint8_t g_xdmac_tx_done, g_xdmac_rx_done;

#endif	/* End of __DRV_SAM_S70_E70_V71_XDMAC_HANDLER_H__ */