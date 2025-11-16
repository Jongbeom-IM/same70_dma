/******************************************************************************
* $ Source $
*
* Workfile: drv_xdmac_usart.c
*
******************************************************************************/

#include <asf.h>

#include "drv_uart_xdmac.h"
#include "drv_xdmac_handler.h"

/******************************************************************************
* DMA State Tracking
******************************************************************************/
typedef struct {
	bool tx_active;
	bool rx_active;
	uint32_t tx_channel;
	uint32_t rx_channel;
} uart_dma_state_t;

/* DMA state for each UART channel */
static uart_dma_state_t uart_dma_states[5] = {0};


#ifdef DEBUG
#include <stdio.h>

#define XDMAC_USART_Debug(x)					//printf x
#define XDMAC_USART_DebugError(x)				printf x
#else
#define XDMAC_USART_Debug(x)
#define XDMAC_USART_DebugError(x)
#endif


/******************************************************************************
* USART DMA Configuration Structure
******************************************************************************/
typedef struct {
	Usart *usart;
	uint32_t tx_channel;
	uint32_t rx_channel;
	uint32_t tx_perid;
	uint32_t rx_perid;
} uart_dma_config_t;

/* USART DMA Configuration Table */
static const uart_dma_config_t uart_dma_configs[] = {
	{
		.usart = UART0,
		.tx_channel = XDMAC_UART0_TX_CH,
		.rx_channel = XDMAC_UART0_RX_CH,
		.tx_perid = UART0_XDMAC_TX_CH_NUM,
		.rx_perid = UART0_XDMAC_RX_CH_NUM
	},
	{
		.usart = UART1,
		.tx_channel = XDMAC_UART1_TX_CH,
		.rx_channel = XDMAC_UART1_RX_CH,
		.tx_perid = UART1_XDMAC_TX_CH_NUM,
		.rx_perid = UART1_XDMAC_RX_CH_NUM
	},
	{
		.usart = UART2,
		.tx_channel = XDMAC_UART2_TX_CH,
		.rx_channel = XDMAC_UART2_RX_CH,
		.tx_perid = UART2_XDMAC_TX_CH_NUM,
		.rx_perid = UART2_XDMAC_RX_CH_NUM
	},
	{
		.usart = UART3,
		.tx_channel = XDMAC_UART3_TX_CH,
		.rx_channel = XDMAC_UART3_RX_CH,
		.tx_perid = UART3_XDMAC_TX_CH_NUM,
		.rx_perid = UART3_XDMAC_RX_CH_NUM
	},
	{
		.usart = UART4,
		.tx_channel = XDMAC_UART4_TX_CH,
		.rx_channel = XDMAC_UART4_RX_CH,
		.tx_perid = UART4_XDMAC_TX_CH_NUM,
		.rx_perid = UART4_XDMAC_RX_CH_NUM
	}
};

#define UART_DMA_CONFIG_COUNT (sizeof(uart_dma_configs) / sizeof(uart_dma_configs[0]))

/** XDMAC channel configuration. */
static xdmac_channel_config_t xdmac_tx_cfg, xdmac_rx_cfg;

/** Helper function to get USART DMA configuration */
static const uart_dma_config_t* get_uart_dma_config(uint8_t channel)
{
	return &uart_dma_configs[channel];
}




/******************************************************************************
* Non-blocking DMA Send Start Function
******************************************************************************/
uint32_t DRV_UART_DMA_Send_Start(Uart *phandle, void *pbuf, uint32_t size)
{
	uint32_t xdmaint;
	const uart_dma_config_t *dma_config;
	uint32_t uart_index;

	if(pbuf == NULL) return 1;

	/* Get UART index and DMA configuration */
	uart_index = GET_UART_CONFIG_INDEX(phandle);
	if (uart_index == 0xFF) return 1;
	
	dma_config = get_uart_dma_config(uart_index);
	if (dma_config == NULL) {
		XDMAC_USART_DebugError(("Unsupported UART for DMA\r\n"));
		return 1;
	}

	/* Check if TX is already active */
	if (uart_dma_states[uart_index].tx_active) {
		XDMAC_USART_DebugError(("UART TX DMA already active\r\n"));
		return 1;
	}

	/* Flush XDMAC interrupt status register */
	(void)(XDMAC->XDMAC_CHID[dma_config->tx_channel].XDMAC_CIS);

	/* Initialize interrupt flags */
	xdmaint = ( XDMAC_CIE_BIE  |
				XDMAC_CIE_DIE  |
				XDMAC_CIE_FIE  |
				XDMAC_CIE_RBIE |
				XDMAC_CIE_WBIE |
				XDMAC_CIE_ROIE);

	/* Initialize channel config for transmitter */
	xdmac_tx_cfg.mbr_ubc = size;
	xdmac_tx_cfg.mbr_sa = (uint32_t)pbuf;
	xdmac_tx_cfg.mbr_da = (uint32_t)&(phandle->UART_THR);
	xdmac_tx_cfg.mbr_cfg =  XDMAC_CC_TYPE_PER_TRAN |
							XDMAC_CC_MBSIZE_SINGLE |
							XDMAC_CC_DSYNC_MEM2PER |
							XDMAC_CC_CSIZE_CHK_1 |
							XDMAC_CC_DWIDTH_BYTE |
							XDMAC_CC_SIF_AHB_IF0 |
							XDMAC_CC_DIF_AHB_IF1 |
							XDMAC_CC_SAM_INCREMENTED_AM |
							XDMAC_CC_DAM_FIXED_AM |
							XDMAC_CC_PERID(dma_config->tx_perid);
	xdmac_tx_cfg.mbr_bc = 0;
	xdmac_tx_cfg.mbr_ds = 0;
	xdmac_tx_cfg.mbr_sus = 0;
	xdmac_tx_cfg.mbr_dus = 0;

	/* Configure and start DMA transfer */
	xdmac_configure_transfer(XDMAC, dma_config->tx_channel, &xdmac_tx_cfg);
	xdmac_channel_set_descriptor_control(XDMAC, dma_config->tx_channel, 0);
	xdmac_channel_enable_interrupt(XDMAC, dma_config->tx_channel, xdmaint);
	
	/* Enable XDMAC interrupt */
	NVIC_ClearPendingIRQ(XDMAC_IRQn);
	NVIC_SetPriority(XDMAC_IRQn, 1);
	NVIC_EnableIRQ(XDMAC_IRQn);
	
	/* Mark as active and start transfer */
	uart_dma_states[uart_index].tx_active = true;
	uart_dma_states[uart_index].tx_channel = dma_config->tx_channel;
	
	xdmac_channel_enable(XDMAC, dma_config->tx_channel);
	xdmac_enable_interrupt(XDMAC, dma_config->tx_channel);

	return 0;
}

/******************************************************************************
* Check if DMA Send is Complete
******************************************************************************/
uint32_t DRV_UART_DMA_Send_IsComplete(Uart *phandle)
{
	uint32_t uart_index;

	uart_index = GET_UART_CONFIG_INDEX(phandle);
	if (uart_index == 0xFF) return 1; /* Error */

	if (!uart_dma_states[uart_index].tx_active) {
		return 1; /* Not active, considered complete */
	}

	/* Check if DMA transfer is complete */
	if (xdmac_is_channel_done(uart_dma_states[uart_index].tx_channel)) {
		/* Transfer complete, cleanup */
		xdmac_clear_channel_flag(uart_dma_states[uart_index].tx_channel);
		xdmac_channel_disable(XDMAC, uart_dma_states[uart_index].tx_channel);
		xdmac_disable_interrupt(XDMAC, uart_dma_states[uart_index].tx_channel);
		uart_dma_states[uart_index].tx_active = false;
		return 1; /* Complete */
	}

	return 0; /* Still in progress */
}

/******************************************************************************
* Abort DMA Send
******************************************************************************/
uint32_t DRV_UART_DMA_Send_Abort(Uart *phandle)
{
	uint32_t uart_index;

	uart_index = GET_UART_CONFIG_INDEX(phandle);
	if (uart_index == 0xFF) return 1;

	if (uart_dma_states[uart_index].tx_active) {
		/* Abort transfer */
		xdmac_channel_disable(XDMAC, uart_dma_states[uart_index].tx_channel);
		xdmac_disable_interrupt(XDMAC, uart_dma_states[uart_index].tx_channel);
		xdmac_clear_channel_flag(uart_dma_states[uart_index].tx_channel);
		uart_dma_states[uart_index].tx_active = false;
	}

	return 0;
}

/******************************************************************************
* Legacy Blocking DMA Send Function (now uses non-blocking internally)
******************************************************************************/
uint32_t DRV_UART_DMA_Send(Uart *phandle, void *pbuf, uint32_t size, uint32_t time_out)
{
	uint32_t result;

	/* Start non-blocking transfer */
	result = DRV_UART_DMA_Send_Start(phandle, pbuf, size);
	if (result != 0) return result;

	/* Wait for completion with timeout */
	while(time_out > 0)
	{
		if(DRV_UART_DMA_Send_IsComplete(phandle))
			return 0; /* Success */

		time_out--;
		delay_us(1);
	}

	/* Timeout occurred, abort transfer */
	DRV_UART_DMA_Send_Abort(phandle);
	return 1; /* Timeout error */
}


/******************************************************************************
* Non-blocking DMA Receive Start Function
******************************************************************************/
uint32_t DRV_UART_DMA_Recv_Start(Uart *phandle, void *pbuf, uint32_t size)
{
	uint32_t xdmaint;
	const uart_dma_config_t *dma_config;
	uint32_t uart_index;

	if(pbuf == NULL) return 1;

	/* Get UART index and DMA configuration */
	uart_index = GET_UART_CONFIG_INDEX(phandle);
	if (uart_index == 0xFF) return 1;
	
	dma_config = get_uart_dma_config(uart_index);
	if (dma_config == NULL) {
		XDMAC_USART_DebugError(("Unsupported UART for DMA\r\n"));
		return 1;
	}

	/* Check if RX is already active */
	if (uart_dma_states[uart_index].rx_active) {
		XDMAC_USART_DebugError(("UART RX DMA already active\r\n"));
		return 1;
	}

	/* Flush UART RHR which is used as XDMAC source address */
	(void)(phandle->UART_RHR);

	/* Flush XDMAC interrupt status register */
	(void)(XDMAC->XDMAC_CHID[dma_config->rx_channel].XDMAC_CIS);

	/* Initialize interrupt flags */
	xdmaint = ( XDMAC_CIE_BIE  |
				XDMAC_CIE_DIE  |
				XDMAC_CIE_FIE  |
				XDMAC_CIE_RBIE |
				XDMAC_CIE_WBIE |
				XDMAC_CIE_ROIE);

	/* Initialize channel config for receiver */
	xdmac_rx_cfg.mbr_ubc = size;
	xdmac_rx_cfg.mbr_sa = (uint32_t)&phandle->UART_RHR;
	xdmac_rx_cfg.mbr_da = (uint32_t)pbuf;
	xdmac_rx_cfg.mbr_cfg =  XDMAC_CC_TYPE_PER_TRAN |
							XDMAC_CC_MBSIZE_SINGLE |
							XDMAC_CC_DSYNC_PER2MEM |
							XDMAC_CC_CSIZE_CHK_1 |
							XDMAC_CC_DWIDTH_BYTE |
							XDMAC_CC_SIF_AHB_IF1 |
							XDMAC_CC_DIF_AHB_IF0 |
							XDMAC_CC_SAM_FIXED_AM |
							XDMAC_CC_DAM_INCREMENTED_AM |
							XDMAC_CC_PERID(dma_config->rx_perid);
	xdmac_rx_cfg.mbr_bc = 0;
	xdmac_rx_cfg.mbr_ds = 0;
	xdmac_rx_cfg.mbr_sus = 0;
	xdmac_rx_cfg.mbr_dus = 0;

	/* Configure and start DMA transfer */
	xdmac_configure_transfer(XDMAC, dma_config->rx_channel, &xdmac_rx_cfg);
	xdmac_channel_set_descriptor_control(XDMAC, dma_config->rx_channel, 0);
	xdmac_channel_enable_interrupt(XDMAC, dma_config->rx_channel, xdmaint);
	
	/* Enable XDMAC interrupt */
	NVIC_ClearPendingIRQ(XDMAC_IRQn);
	NVIC_SetPriority(XDMAC_IRQn, 1);
	NVIC_EnableIRQ(XDMAC_IRQn);
	
	/* Mark as active and start transfer */
	uart_dma_states[uart_index].rx_active = true;
	uart_dma_states[uart_index].rx_channel = dma_config->rx_channel;
	
	xdmac_channel_enable(XDMAC, dma_config->rx_channel);
	xdmac_enable_interrupt(XDMAC, dma_config->rx_channel);

	return 0;
}

/******************************************************************************
* Check if DMA Receive is Complete
******************************************************************************/
uint32_t DRV_UART_DMA_Recv_IsComplete(Uart *phandle)
{
	uint32_t uart_index;

	uart_index = GET_UART_CONFIG_INDEX(phandle);
	if (uart_index == 0xFF) return 1; /* Error */

	if (!uart_dma_states[uart_index].rx_active) {
		return 1; /* Not active, considered complete */
	}

	/* Check if DMA transfer is complete */
	if (xdmac_is_channel_done(uart_dma_states[uart_index].rx_channel)) {
		/* Transfer complete, cleanup */
		xdmac_clear_channel_flag(uart_dma_states[uart_index].rx_channel);
		xdmac_channel_disable(XDMAC, uart_dma_states[uart_index].rx_channel);
		xdmac_disable_interrupt(XDMAC, uart_dma_states[uart_index].rx_channel);
		uart_dma_states[uart_index].rx_active = false;
		return 1; /* Complete */
	}

	return 0; /* Still in progress */
}

/******************************************************************************
* Abort DMA Receive
******************************************************************************/
uint32_t DRV_UART_DMA_Recv_Abort(Uart *phandle)
{
	uint32_t uart_index;

	uart_index = GET_UART_CONFIG_INDEX(phandle);
	if (uart_index == 0xFF) return 1;

	if (uart_dma_states[uart_index].rx_active) {
		/* Abort transfer */
		xdmac_channel_disable(XDMAC, uart_dma_states[uart_index].rx_channel);
		xdmac_disable_interrupt(XDMAC, uart_dma_states[uart_index].rx_channel);
		xdmac_clear_channel_flag(uart_dma_states[uart_index].rx_channel);
		uart_dma_states[uart_index].rx_active = false;
	}

	return 0;
}

/******************************************************************************
* Legacy Blocking DMA Receive Function (now uses non-blocking internally)
******************************************************************************/
uint32_t DRV_UART_DMA_Recv(Uart *phandle, void *pbuf, uint32_t size, uint32_t time_out)
{
	uint32_t result;

	/* Start non-blocking transfer */
	result = DRV_UART_DMA_Recv_Start(phandle, pbuf, size);
	if (result != 0) return result;

	/* Wait for completion with timeout */
	while(time_out > 0)
	{
		if(DRV_UART_DMA_Recv_IsComplete(phandle))
			return 0; /* Success */

		time_out--;
		delay_us(1);
	}

	/* Timeout occurred, abort transfer */
	DRV_UART_DMA_Recv_Abort(phandle);
	return 1; /* Timeout error */
}

/* End of File */
