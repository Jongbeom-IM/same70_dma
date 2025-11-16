/******************************************************************************
* Message Parser for SAME70 XDMAC USART/UART Communication
*
* Message Protocol Structure:
* [SENSOR_ID(1)] [LENGTH(1)] [DATA(N)] [CRC(1)]
*
* SENSOR_ID: 0x01~0x06 (6 sensors)
* LENGTH: Data length (excluding header and CRC)
* DATA: Actual message data
* CRC: Simple checksum for data integrity
******************************************************************************/

#include <asf.h>
#include <string.h>
#include "message_parser.h"

#ifdef DEBUG
#include <stdio.h>
#define MSG_Debug(x)    printf x
#define MSG_DebugError(x) printf x
#else
#define MSG_Debug(x)
#define MSG_DebugError(x)
#endif

/******************************************************************************
* Global Variables
******************************************************************************/
static message_parser_state_t parser_states[MAX_CHANNELS];
static uint32_t total_messages_parsed = 0;
static uint32_t total_crc_errors = 0;

/******************************************************************************
* Static Function Prototypes
******************************************************************************/
static uint8_t calculate_crc(const uint8_t *data, uint8_t length);
static bool is_valid_sensor_id(uint8_t sensor_id);
static void reset_parser_state(message_parser_state_t *state);

/******************************************************************************
* CRC Calculation (Simple checksum)
******************************************************************************/
static uint8_t calculate_crc(const uint8_t *data, uint8_t length)
{
    uint8_t crc = 0;
    for (uint8_t i = 0; i < length; i++) {
        crc ^= data[i];
    }
    return crc;
}

/******************************************************************************
* Validate Sensor ID
******************************************************************************/
static bool is_valid_sensor_id(uint8_t sensor_id)
{
    return (sensor_id >= SENSOR_ID_MIN && sensor_id <= SENSOR_ID_MAX);
}

/******************************************************************************
* Reset Parser State
******************************************************************************/
static void reset_parser_state(message_parser_state_t *state)
{
    state->state = MSG_STATE_WAIT_SENSOR_ID;
    state->bytes_received = 0;
    state->expected_length = 0;
    memset(state->buffer, 0, sizeof(state->buffer));
}

/******************************************************************************
* Initialize Message Parser
******************************************************************************/
void message_parser_init(void)
{
    for (int i = 0; i < MAX_CHANNELS; i++) {
        reset_parser_state(&parser_states[i]);
        parser_states[i].channel_id = i;
    }
    
    total_messages_parsed = 0;
    total_crc_errors = 0;
    
    MSG_Debug(("Message Parser initialized for %d channels\r\n", MAX_CHANNELS));
}

/******************************************************************************
* Parse Received Bytes
******************************************************************************/
message_parse_result_t message_parser_process(uint8_t channel_id, const uint8_t *data, uint8_t length)
{
    if (channel_id >= MAX_CHANNELS) {
        MSG_DebugError(("Invalid channel ID: %d\r\n", channel_id));
        return MSG_PARSE_ERROR;
    }
    
    message_parser_state_t *state = &parser_states[channel_id];
    message_parse_result_t result = MSG_PARSE_INCOMPLETE;
    
    for (uint8_t i = 0; i < length; i++) {
        uint8_t byte = data[i];
        
        switch (state->state) {
            case MSG_STATE_WAIT_SENSOR_ID:
                if (is_valid_sensor_id(byte)) {
                    state->buffer[0] = byte;
                    state->bytes_received = 1;
                    state->state = MSG_STATE_WAIT_LENGTH;
                    MSG_Debug(("Ch%d: Sensor ID 0x%02X received\r\n", channel_id, byte));
                } else {
                    MSG_DebugError(("Ch%d: Invalid sensor ID: 0x%02X\r\n", channel_id, byte));
                    reset_parser_state(state);
                }
                break;
                
            case MSG_STATE_WAIT_LENGTH:
                if (byte <= MAX_MESSAGE_DATA_SIZE) {
                    state->buffer[1] = byte;
                    state->expected_length = byte;
                    state->bytes_received = 2;
                    
                    if (byte == 0) {
                        // No data, go directly to CRC
                        state->state = MSG_STATE_WAIT_CRC;
                    } else {
                        state->state = MSG_STATE_WAIT_DATA;
                    }
                    MSG_Debug(("Ch%d: Data length %d\r\n", channel_id, byte));
                } else {
                    MSG_DebugError(("Ch%d: Invalid length: %d\r\n", channel_id, byte));
                    reset_parser_state(state);
                }
                break;
                
            case MSG_STATE_WAIT_DATA:
                state->buffer[state->bytes_received++] = byte;
                if (state->bytes_received >= (2 + state->expected_length)) {
                    state->state = MSG_STATE_WAIT_CRC;
                }
                break;
                
            case MSG_STATE_WAIT_CRC:
                state->buffer[state->bytes_received++] = byte;
                
                // Calculate CRC for sensor_id + length + data
                uint8_t calculated_crc = calculate_crc(state->buffer, state->bytes_received - 1);
                
                if (calculated_crc == byte) {
                    // Message complete and valid
                    total_messages_parsed++;
                    result = MSG_PARSE_COMPLETE;
                    MSG_Debug(("Ch%d: Message complete! Sensor=0x%02X, Len=%d, CRC=OK\r\n", 
                              channel_id, state->buffer[0], state->expected_length));
                } else {
                    // CRC error
                    total_crc_errors++;
                    result = MSG_PARSE_CRC_ERROR;
                    MSG_DebugError(("Ch%d: CRC error! Expected=0x%02X, Got=0x%02X\r\n", 
                                   channel_id, calculated_crc, byte));
                }
                
                reset_parser_state(state);
                return result; // Return immediately after processing complete message
        }
    }
    
    return MSG_PARSE_INCOMPLETE;
}

/******************************************************************************
* Get Current Message
******************************************************************************/
bool message_parser_get_message(uint8_t channel_id, parsed_message_t *message)
{
    if (channel_id >= MAX_CHANNELS || message == NULL) {
        return false;
    }
    
    message_parser_state_t *state = &parser_states[channel_id];
    
    if (state->bytes_received < 3) { // At least sensor_id + length + crc
        return false;
    }
    
    message->sensor_id = state->buffer[0];
    message->data_length = state->buffer[1];
    message->channel_id = channel_id;
    
    if (message->data_length > 0) {
        memcpy(message->data, &state->buffer[2], message->data_length);
    }
    
    return true;
}

/******************************************************************************
* Create Message
******************************************************************************/
uint8_t message_parser_create_message(uint8_t sensor_id, const uint8_t *data, 
                                     uint8_t data_length, uint8_t *output_buffer)
{
    if (!is_valid_sensor_id(sensor_id) || 
        data_length > MAX_MESSAGE_DATA_SIZE || 
        output_buffer == NULL) {
        return 0;
    }
    
    // Build message: [SENSOR_ID][LENGTH][DATA][CRC]
    output_buffer[0] = sensor_id;
    output_buffer[1] = data_length;
    
    if (data_length > 0 && data != NULL) {
        memcpy(&output_buffer[2], data, data_length);
    }
    
    // Calculate CRC for sensor_id + length + data
    uint8_t crc = calculate_crc(output_buffer, 2 + data_length);
    output_buffer[2 + data_length] = crc;
    
    return 3 + data_length; // Total message length
}

/******************************************************************************
* Get Parser Statistics
******************************************************************************/
void message_parser_get_stats(parser_stats_t *stats)
{
    if (stats == NULL) return;
    
    stats->total_messages_parsed = total_messages_parsed;
    stats->total_crc_errors = total_crc_errors;
    stats->success_rate = (total_messages_parsed > 0) ? 
        ((total_messages_parsed * 100) / (total_messages_parsed + total_crc_errors)) : 0;
    
    // Count messages in progress
    stats->messages_in_progress = 0;
    for (int i = 0; i < MAX_CHANNELS; i++) {
        if (parser_states[i].state != MSG_STATE_WAIT_SENSOR_ID) {
            stats->messages_in_progress++;
        }
    }
}

/******************************************************************************
* Reset Parser for Specific Channel
******************************************************************************/
void message_parser_reset_channel(uint8_t channel_id)
{
    if (channel_id < MAX_CHANNELS) {
        reset_parser_state(&parser_states[channel_id]);
        MSG_Debug(("Parser reset for channel %d\r\n", channel_id));
    }
}

/******************************************************************************
* Get Sensor Name String
******************************************************************************/
const char* message_parser_get_sensor_name(uint8_t sensor_id)
{
    switch (sensor_id) {
        case 0x01: return "Temperature";
        case 0x02: return "Humidity";
        case 0x03: return "Pressure";
        case 0x04: return "Light";
        case 0x05: return "Motion";
        case 0x06: return "Sound";
        default: return "Unknown";
    }
}

/******************************************************************************
* Print Message in Human-Readable Format
******************************************************************************/
void message_parser_print_message(const parsed_message_t *message)
{
    if (message == NULL) return;
    
    MSG_Debug(("=== Message from Channel %d ===\r\n", message->channel_id));
    MSG_Debug(("Sensor: %s (0x%02X)\r\n", 
              message_parser_get_sensor_name(message->sensor_id), 
              message->sensor_id));
    MSG_Debug(("Data Length: %d bytes\r\n", message->data_length));
    
    if (message->data_length > 0) {
        MSG_Debug(("Data: "));
        for (uint8_t i = 0; i < message->data_length; i++) {
            MSG_Debug(("0x%02X ", message->data[i]));
        }
        MSG_Debug(("\r\n"));
        
        // Try to print as string if printable
        bool is_printable = true;
        for (uint8_t i = 0; i < message->data_length; i++) {
            if (message->data[i] < 32 || message->data[i] > 126) {
                is_printable = false;
                break;
            }
        }
        
        if (is_printable) {
            MSG_Debug(("ASCII: \""));
            for (uint8_t i = 0; i < message->data_length; i++) {
                MSG_Debug(("%c", message->data[i]));
            }
            MSG_Debug(("\"\r\n"));
        }
    }
    MSG_Debug(("========================\r\n"));
}

/* End of File */