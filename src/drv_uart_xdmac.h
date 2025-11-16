#ifndef __DRV_SAM_S70_E70_V71_XDMAC_USART_H__
#define __DRV_SAM_S70_E70_V71_XDMAC_USART_H__


/******************************************************************************
* include
******************************************************************************/

#include "asf.h"


/******************************************************************************
* MACRO
******************************************************************************/

#define GET_UART_CONFIG_INDEX(usart) \
    ((usart == UART0)  ? 0 : \
     (usart == UART1)  ? 1 : \
     (usart == UART2)  ? 2 : \
     (usart == UART3)  ? 3 : \
     (usart == UART4)  ? 4 : 0xFF)
/******************************************************************************
* Functions
******************************************************************************/

/* Blocking DMA Functions (legacy) */
extern uint32_t DRV_UART_DMA_Send(Uart *, void *, uint32_t, uint32_t);
extern uint32_t DRV_UART_DMA_Recv(Uart *, void *, uint32_t, uint32_t);

/* Non-blocking DMA Functions */
extern uint32_t DRV_UART_DMA_Send_Start(Uart *, void *, uint32_t);
extern uint32_t DRV_UART_DMA_Recv_Start(Uart *, void *, uint32_t);
extern uint32_t DRV_UART_DMA_Send_IsComplete(Uart *);
extern uint32_t DRV_UART_DMA_Recv_IsComplete(Uart *);
extern uint32_t DRV_UART_DMA_Send_Abort(Uart *);
extern uint32_t DRV_UART_DMA_Recv_Abort(Uart *);

#endif	/* End of __DRV_SAM_S70_E70_V71_XDMAC_USART_H__ */