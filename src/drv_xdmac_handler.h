#ifndef __DRV_SAM_S70_E70_V71_XDMAC_HANDLER_H__
#define __DRV_SAM_S70_E70_V71_XDMAC_HANDLER_H__


/******************************************************************************
* include
******************************************************************************/

#include "asf.h"


/******************************************************************************
* MACRO
******************************************************************************/

/** Physical XDMAC channel used in this example. */
#define XDMAC_USART0_TX_CH				1
#define XDMAC_USART0_RX_CH				2
#define XDMAC_USART1_TX_CH				3
#define XDMAC_USART1_RX_CH				4

#define SPI0_XDMAC_TX_CH_NUM			1
#define SPI0_XDMAC_RX_CH_NUM			2
#define SPI1_XDMAC_TX_CH_NUM			3
#define SPI1_XDMAC_RX_CH_NUM			4
#define QSPI_XDMAC_TX_CH_NUM			5
#define QSPI_XDMAC_RX_CH_NUM			6
#define USART0_XDMAC_TX_CH_NUM			7
#define USART0_XDMAC_RX_CH_NUM			8
#define USART1_XDMAC_TX_CH_NUM			9
#define USART1_XDMAC_RX_CH_NUM			10
#define USART2_XDMAC_TX_CH_NUM			11
#define USART2_XDMAC_RX_CH_NUM			12
#define PWM_XDMAC_TX_CH_NUM			    13
#define TWIHS0_XDMAC_TX_CH_NUM          14
#define TWIHS0_XDMAC_RX_CH_NUM          15
#define TWIHS1_XDMAC_TX_CH_NUM          16
#define TWIHS1_XDMAC_TX_CH_NUM          17
#define TWIHS2_XDMAC_TX_CH_NUM          18
#define TWIHS2_XDMAC_TX_CH_NUM          19
#define UART0_XDMAC_TX_CH_NUM			20
#define UART0_XDMAC_RX_CH_NUM			21
#define UART1_XDMAC_TX_CH_NUM			22
#define UART1_XDMAC_RX_CH_NUM			23
#define UART2_XDMAC_TX_CH_NUM			24
#define UART2_XDMAC_RX_CH_NUM			25
#define UART3_XDMAC_TX_CH_NUM			26
#define UART3_XDMAC_RX_CH_NUM			27
#define UART4_XDMAC_TX_CH_NUM			28
#define UART4_XDMAC_RX_CH_NUM			29
#define DACC_XDMAC_TX_CH_NUM            30
#define SSC_XDMAC_TX_CH_NUM             32
#define SSC_XDMAC_RX_CH_NUM             33
#define PIOA_XDMAC_RX_CH_NUM            34
#define 



/******************************************************************************
* Variables
******************************************************************************/

extern volatile uint8_t g_xdmac_tx_done, g_xdmac_rx_done;

#endif	/* End of __DRV_SAM_S70_E70_V71_XDMAC_HANDLER_H__ */