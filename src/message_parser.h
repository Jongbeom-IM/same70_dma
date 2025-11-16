/******************************************************************************
* Message Parser Header for SAME70 XDMAC USART/UART Communication
*
* Protocol: [SENSOR_ID(1)] [LENGTH(1)] [DATA(N)] [CRC(1)]
******************************************************************************/

#ifndef __MESSAGE_PARSER_H__
#define __MESSAGE_PARSER_H__

#include <stdint.h>
#include <stdbool.h>

/******************************************************************************
* Constants
******************************************************************************/
#define MAX_CHANNELS            8       // USART0-2, UART0-4
#define MAX_MESSAGE_DATA_SIZE   64      // Maximum data payload size
#define MAX_MESSAGE_SIZE        (MAX_MESSAGE_DATA_SIZE + 3)  // +3 for header and CRC

#define SENSOR_ID_MIN           0x01
#define SENSOR_ID_MAX           0x06

/******************************************************************************
* Message Parser States
******************************************************************************/
typedef enum {
    MSG_STATE_WAIT_SENSOR_ID = 0,
    MSG_STATE_WAIT_LENGTH,
    MSG_STATE_WAIT_DATA,
    MSG_STATE_WAIT_CRC
} message_state_t;

/******************************************************************************
* Parse Results
******************************************************************************/
typedef enum {
    MSG_PARSE_INCOMPLETE = 0,   // Need more data
    MSG_PARSE_COMPLETE,         // Message successfully parsed
    MSG_PARSE_CRC_ERROR,        // CRC validation failed
    MSG_PARSE_ERROR            // General parsing error
} message_parse_result_t;

/******************************************************************************
* Sensor IDs
******************************************************************************/
typedef enum {
    SENSOR_TEMPERATURE = 0x01,
    SENSOR_HUMIDITY    = 0x02,
    SENSOR_PRESSURE    = 0x03,
    SENSOR_LIGHT       = 0x04,
    SENSOR_MOTION      = 0x05,
    SENSOR_SOUND       = 0x06
} sensor_id_t;

/******************************************************************************
* Structures
******************************************************************************/
typedef struct {
    message_state_t state;
    uint8_t channel_id;
    uint8_t buffer[MAX_MESSAGE_SIZE];
    uint8_t bytes_received;
    uint8_t expected_length;
} message_parser_state_t;

typedef struct {
    uint8_t sensor_id;
    uint8_t data_length;
    uint8_t data[MAX_MESSAGE_DATA_SIZE];
    uint8_t channel_id;
} parsed_message_t;

typedef struct {
    uint32_t total_messages_parsed;
    uint32_t total_crc_errors;
    uint32_t success_rate;      // percentage
    uint8_t messages_in_progress;
} parser_stats_t;

/******************************************************************************
* Function Prototypes
******************************************************************************/

/**
 * Initialize the message parser system
 */
void message_parser_init(void);

/**
 * Process received bytes for a specific channel
 * @param channel_id Channel ID (0-7)
 * @param data Received data buffer
 * @param length Number of bytes received
 * @return Parse result
 */
message_parse_result_t message_parser_process(uint8_t channel_id, 
                                            const uint8_t *data, 
                                            uint8_t length);

/**
 * Get the current parsed message for a channel
 * @param channel_id Channel ID (0-7)
 * @param message Output message structure
 * @return true if valid message available
 */
bool message_parser_get_message(uint8_t channel_id, parsed_message_t *message);

/**
 * Create a message packet
 * @param sensor_id Sensor identifier (0x01-0x06)
 * @param data Data payload (can be NULL if data_length is 0)
 * @param data_length Length of data payload
 * @param output_buffer Output buffer for complete message
 * @return Total message length (including header and CRC)
 */
uint8_t message_parser_create_message(uint8_t sensor_id, 
                                     const uint8_t *data,
                                     uint8_t data_length, 
                                     uint8_t *output_buffer);

/**
 * Get parser statistics
 * @param stats Output statistics structure
 */
void message_parser_get_stats(parser_stats_t *stats);

/**
 * Reset parser state for a specific channel
 * @param channel_id Channel ID to reset
 */
void message_parser_reset_channel(uint8_t channel_id);

/**
 * Get sensor name string
 * @param sensor_id Sensor ID
 * @return Human-readable sensor name
 */
const char* message_parser_get_sensor_name(uint8_t sensor_id);

/**
 * Print message in human-readable format
 * @param message Message to print
 */
void message_parser_print_message(const parsed_message_t *message);

/******************************************************************************
* Inline Helper Functions
******************************************************************************/

/**
 * Check if sensor ID is valid
 */
static inline bool message_parser_is_valid_sensor_id(uint8_t sensor_id)
{
    return (sensor_id >= SENSOR_ID_MIN && sensor_id <= SENSOR_ID_MAX);
}

/**
 * Get channel ID from USART pointer
 */
static inline uint8_t message_parser_get_usart_channel_id(Usart *usart)
{
    if (usart == USART0) return 0;
    if (usart == USART1) return 1;
    if (usart == USART2) return 2;
    return 0xFF; // Invalid
}

/**
 * Get channel ID from UART pointer
 */
static inline uint8_t message_parser_get_uart_channel_id(Uart *uart)
{
    if (uart == UART0) return 3;
    if (uart == UART1) return 4;
    if (uart == UART2) return 5;
    if (uart == UART3) return 6;
    if (uart == UART4) return 7;
    return 0xFF; // Invalid
}

#endif /* __MESSAGE_PARSER_H__ */