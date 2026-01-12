/******************************************************************************
* Message Parser Header for SAME70 XDMAC USART/UART Communication
*
* Protocol: [SENSOR_ID(1)] [LENGTH(1)] [DATA(N)] [CRC(1)]
******************************************************************************/

#ifndef __MESSAGE_PARSER_H__
#define __MESSAGE_PARSER_H__

#include <stdint.h>
#include <stdbool.h>

