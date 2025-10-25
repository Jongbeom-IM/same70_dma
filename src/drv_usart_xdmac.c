/******************************************************************************
* $ Source $
*
* Workfile: drv_xdmac_usart.c
*
******************************************************************************/

#include <asf.h>

#include "drv_usart_xdmac.h"
#include "drv_xdmac_handler.h"


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
} usart_dma_config_t;

/* USART DMA Configuration Table */
static const usart_dma_config_t usart_dma_configs[] = {
	{
		.usart = USART0,
		.tx_channel = XDMAC_USART0_TX_CH,
		.rx_channel = XDMAC_USART0_RX_CH,
		.tx_perid = USART0_XDMAC_TX_CH_NUM,
		.rx_perid = USART0_XDMAC_RX_CH_NUM
	},
	{
		.usart = USART1,
		.tx_channel = XDMAC_USART1_TX_CH,
		.rx_channel = XDMAC_USART1_RX_CH,
		.tx_perid = USART1_XDMAC_TX_CH_NUM,
		.rx_perid = USART1_XDMAC_RX_CH_NUM
	}
};

#define USART_DMA_CONFIG_COUNT (sizeof(usart_dma_configs) / sizeof(usart_dma_configs[0]))

/** XDMAC channel configuration. */
static xdmac_channel_config_t xdmac_tx_cfg, xdmac_rx_cfg;

/** Helper function to get USART DMA configuration */
static const usart_dma_config_t* get_usart_dma_config(Usart *pusart)
{
	for (uint32_t i = 0; i < USART_DMA_CONFIG_COUNT; i++) {
		if (usart_dma_configs[i].usart == pusart) {
			return &usart_dma_configs[i];
		}
	}
	return NULL;
}




uint32_t DRV_USART_DMA_Send(Usart *phandle, void *pbuf, uint32_t size, uint32_t time_out)
{
	uint32_t xdmaint;
	const usart_dma_config_t *dma_config;

	if(pbuf == NULL) return 1;

	/* Get DMA configuration for this USART */
	dma_config = get_usart_dma_config(phandle);
	if (dma_config == NULL) {
		XDMAC_USART_DebugError(("Unsupported USART for DMA\r\n"));
		return 1;
	}

	g_xdmac_tx_done = 0;

	/* Flush XDMAC interrupt status register */
	(void)(XDMAC->XDMAC_CHID[dma_config->tx_channel].XDMAC_CIS);

	/* Initialize and enable DMA controller : */
	/* Initialize interrupt flag in the XDMAC Channel x Interrupt Enable Register */
	xdmaint = ( XDMAC_CIE_BIE  |
				XDMAC_CIE_DIE  |
				XDMAC_CIE_FIE  |
				XDMAC_CIE_RBIE |
				XDMAC_CIE_WBIE |
				XDMAC_CIE_ROIE);

	/* Initialize channel config for transmitter */
	xdmac_tx_cfg.mbr_ubc = size;

	xdmac_tx_cfg.mbr_sa = (uint32_t)pbuf;
	xdmac_tx_cfg.mbr_da = (uint32_t)&(phandle->US_THR);

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

	xdmac_configure_transfer(XDMAC, dma_config->tx_channel, &xdmac_tx_cfg);

	xdmac_channel_set_descriptor_control(XDMAC, dma_config->tx_channel, 0);
	xdmac_channel_enable_interrupt(XDMAC, dma_config->tx_channel, xdmaint);
	xdmac_channel_enable(XDMAC, dma_config->tx_channel);

	xdmac_enable_interrupt(XDMAC, dma_config->tx_channel);

	/* Enable XDMAC interrupt */
	NVIC_ClearPendingIRQ(XDMAC_IRQn);
	NVIC_SetPriority(XDMAC_IRQn, 1);
	NVIC_EnableIRQ(XDMAC_IRQn);

	while(time_out > 0)
	{
		if(g_xdmac_tx_done == 1)
			break;

		time_out--;
		delay_us(1);
	}

	g_xdmac_tx_done = 0;

	xdmac_channel_disable_interrupt(XDMAC, dma_config->tx_channel, xdmaint);
	xdmac_channel_disable(XDMAC, dma_config->tx_channel);
	xdmac_disable_interrupt(XDMAC, dma_config->tx_channel);

	NVIC_ClearPendingIRQ(XDMAC_IRQn);
	NVIC_DisableIRQ(XDMAC_IRQn);

	if(time_out == 0)
		return 1;


	return 0;
}




uint32_t DRV_USART_DMA_Recv(Usart *phandle, void *pbuf, uint32_t size, uint32_t time_out)
{
	uint32_t xdmaint;
	const usart_dma_config_t *dma_config;

	if(pbuf == NULL) return 1;

	/* Get DMA configuration for this USART */
	dma_config = get_usart_dma_config(phandle);
	if (dma_config == NULL) {
		XDMAC_USART_DebugError(("Unsupported USART for DMA\r\n"));
		return 1;
	}

	g_xdmac_rx_done = 0;

	/* Flush USART RHR which is used as XDMAC source address */
	(void)(phandle->US_RHR);

	/* Flush XDMAC interrupt status register */
	(void)(XDMAC->XDMAC_CHID[dma_config->rx_channel].XDMAC_CIS);

	/* Initialize and enable DMA controller : */
	/* Initialize interrupt flag in the XDMAC Channel x Interrupt Enable Register */
	xdmaint = ( XDMAC_CIE_BIE  |
				XDMAC_CIE_DIE  |
				XDMAC_CIE_FIE  |
				XDMAC_CIE_RBIE |
				XDMAC_CIE_WBIE |
				XDMAC_CIE_ROIE);

	/* Initialize channel config for receiver */
	xdmac_rx_cfg.mbr_ubc = size;

	xdmac_rx_cfg.mbr_sa = (uint32_t)&phandle->US_RHR;
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

	xdmac_configure_transfer(XDMAC, dma_config->rx_channel, &xdmac_rx_cfg);

	xdmac_channel_set_descriptor_control(XDMAC, dma_config->rx_channel, 0);
	xdmac_channel_enable_interrupt(XDMAC, dma_config->rx_channel, xdmaint);
	xdmac_channel_enable(XDMAC, dma_config->rx_channel);

	xdmac_enable_interrupt(XDMAC, dma_config->rx_channel);

	/* Enable XDMAC interrupt */
	NVIC_ClearPendingIRQ(XDMAC_IRQn);
	NVIC_SetPriority(XDMAC_IRQn, 1);
	NVIC_EnableIRQ(XDMAC_IRQn);

	while(time_out > 0)
	{
		if(g_xdmac_rx_done == 1)
			break;

		time_out--;
		delay_us(1);
	}

	g_xdmac_rx_done = 0;

	xdmac_channel_disable_interrupt(XDMAC, dma_config->rx_channel, xdmaint);
	xdmac_channel_disable(XDMAC, dma_config->rx_channel);
	xdmac_disable_interrupt(XDMAC, dma_config->rx_channel);

	NVIC_ClearPendingIRQ(XDMAC_IRQn);
	NVIC_DisableIRQ(XDMAC_IRQn);

	if(time_out == 0)
		return 1;


	return 0;
}

/* End of File */
