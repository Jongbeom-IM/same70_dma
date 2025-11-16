/******************************************************************************
* Message Parser Demo for SAME70 Non-Blocking DMA
*
* This demo shows how to use the message parser with non-blocking DMA
* to handle structured messages from multiple sensors across 8 channels.
******************************************************************************/

#include <asf.h>
#include <string.h>
#include "message_parser.h"
#include "drv_usart_xdmac.h"
#include "drv_uart_xdmac.h"
#include "drv_usart.h"

#ifdef DEBUG
#include <stdio.h>
#define DEMO_Debug(x)    printf x
#define DEMO_DebugError(x) printf x
#else
#define DEMO_Debug(x)
#define DEMO_DebugError(x)
#endif

/******************************************************************************
* Demo Configuration
******************************************************************************/
#define RX_BUFFER_SIZE  MAX_MESSAGE_SIZE
#define TX_BUFFER_SIZE  MAX_MESSAGE_SIZE

/******************************************************************************
* Global Buffers for Each Channel
******************************************************************************/
static uint8_t rx_buffers[MAX_CHANNELS][RX_BUFFER_SIZE];
static uint8_t tx_buffers[MAX_CHANNELS][TX_BUFFER_SIZE];
static bool channel_rx_active[MAX_CHANNELS] = {false};

/******************************************************************************
* Sample Sensor Data Generation
******************************************************************************/
static void generate_sample_sensor_data(uint8_t sensor_id, uint8_t *data, uint8_t *length)
{
    switch (sensor_id) {
        case SENSOR_TEMPERATURE:
            data[0] = 25; // 25°C
            data[1] = 5;  // .5°C
            *length = 2;
            break;
            
        case SENSOR_HUMIDITY:
            data[0] = 60; // 60%
            *length = 1;
            break;
            
        case SENSOR_PRESSURE:
            data[0] = 0x03; // 1013 hPa (big-endian)
            data[1] = 0xF5;
            *length = 2;
            break;
            
        case SENSOR_LIGHT:
            data[0] = 0x4E; // 1250 lux
            data[1] = 0x20;
            *length = 2;
            break;
            
        case SENSOR_MOTION:
            data[0] = 1; // Motion detected
            *length = 1;
            break;
            
        case SENSOR_SOUND:
            data[0] = 45; // 45 dB
            *length = 1;
            break;
            
        default:
            *length = 0;
            break;
    }
}

/******************************************************************************
* Send Test Messages to All Channels
******************************************************************************/
static void send_test_messages(void)
{
    DEMO_Debug(("=== Sending Test Messages ===\r\n"));
    
    for (uint8_t ch = 0; ch < MAX_CHANNELS; ch++) {
        uint8_t sensor_id = (ch % 6) + 1; // Sensors 1-6, cycling
        uint8_t sensor_data[MAX_MESSAGE_DATA_SIZE];
        uint8_t data_length;
        
        // Generate sample data for this sensor
        generate_sample_sensor_data(sensor_id, sensor_data, &data_length);
        
        // Create message packet
        uint8_t msg_length = message_parser_create_message(sensor_id, 
                                                         sensor_data, 
                                                         data_length, 
                                                         tx_buffers[ch]);
        
        if (msg_length > 0) {
            // Send via appropriate channel
            uint32_t result = 1;
            if (ch < 3) {
                // USART channels (0-2)
                Usart *usart = (ch == 0) ? USART0 : (ch == 1) ? USART1 : USART2;
                result = DRV_USART_DMA_Send_Start(usart, tx_buffers[ch], msg_length);
            } else {
                // UART channels (3-7)
                Uart *uart = (ch == 3) ? UART0 : (ch == 4) ? UART1 : 
                            (ch == 5) ? UART2 : (ch == 6) ? UART3 : UART4;
                result = DRV_UART_DMA_Send_Start(uart, tx_buffers[ch], msg_length);
            }
            
            if (result == 0) {
                DEMO_Debug(("Ch%d: Sent %s sensor data (%d bytes)\r\n", 
                           ch, message_parser_get_sensor_name(sensor_id), msg_length));
            } else {
                DEMO_DebugError(("Ch%d: Failed to start DMA send\r\n", ch));
            }
        }
    }
}

/******************************************************************************
* Start Receive Operations on All Channels
******************************************************************************/
static void start_receive_operations(void)
{
    DEMO_Debug(("=== Starting Receive Operations ===\r\n"));
    
    for (uint8_t ch = 0; ch < MAX_CHANNELS; ch++) {
        uint32_t result = 1;
        
        if (ch < 3) {
            // USART channels (0-2)
            Usart *usart = (ch == 0) ? USART0 : (ch == 1) ? USART1 : USART2;
            result = DRV_USART_DMA_Recv_Start(usart, rx_buffers[ch], RX_BUFFER_SIZE);
        } else {
            // UART channels (3-7)
            Uart *uart = (ch == 3) ? UART0 : (ch == 4) ? UART1 : 
                        (ch == 5) ? UART2 : (ch == 6) ? UART3 : UART4;
            result = DRV_UART_DMA_Recv_Start(uart, rx_buffers[ch], RX_BUFFER_SIZE);
        }
        
        if (result == 0) {
            channel_rx_active[ch] = true;
            DEMO_Debug(("Ch%d: Receive started\r\n", ch));
        } else {
            DEMO_DebugError(("Ch%d: Failed to start DMA receive\r\n", ch));
        }
    }
}

/******************************************************************************
* Check for Received Messages
******************************************************************************/
static void check_received_messages(void)
{
    for (uint8_t ch = 0; ch < MAX_CHANNELS; ch++) {
        if (!channel_rx_active[ch]) continue;
        
        bool rx_complete = false;
        
        if (ch < 3) {
            // USART channels (0-2)
            Usart *usart = (ch == 0) ? USART0 : (ch == 1) ? USART1 : USART2;
            rx_complete = DRV_USART_DMA_Recv_IsComplete(usart);
        } else {
            // UART channels (3-7)
            Uart *uart = (ch == 3) ? UART0 : (ch == 4) ? UART1 : 
                        (ch == 5) ? UART2 : (ch == 6) ? UART3 : UART4;
            rx_complete = DRV_UART_DMA_Recv_IsComplete(uart);
        }
        
        if (rx_complete) {
            channel_rx_active[ch] = false;
            
            // Process received data with message parser
            message_parse_result_t result = message_parser_process(ch, 
                                                                 rx_buffers[ch], 
                                                                 RX_BUFFER_SIZE);
            
            switch (result) {
                case MSG_PARSE_COMPLETE:
                    {
                        parsed_message_t message;
                        if (message_parser_get_message(ch, &message)) {
                            DEMO_Debug(("Ch%d: Message received!\r\n", ch));
                            message_parser_print_message(&message);
                        }
                    }
                    break;
                    
                case MSG_PARSE_CRC_ERROR:
                    DEMO_DebugError(("Ch%d: CRC error in received message\r\n", ch));
                    break;
                    
                case MSG_PARSE_ERROR:
                    DEMO_DebugError(("Ch%d: Parse error in received message\r\n", ch));
                    break;
                    
                case MSG_PARSE_INCOMPLETE:
                    DEMO_Debug(("Ch%d: Incomplete message received\r\n", ch));
                    break;
            }
            
            // Restart receive for this channel
            uint32_t restart_result = 1;
            if (ch < 3) {
                Usart *usart = (ch == 0) ? USART0 : (ch == 1) ? USART1 : USART2;
                restart_result = DRV_USART_DMA_Recv_Start(usart, rx_buffers[ch], RX_BUFFER_SIZE);
            } else {
                Uart *uart = (ch == 3) ? UART0 : (ch == 4) ? UART1 : 
                            (ch == 5) ? UART2 : (ch == 6) ? UART3 : UART4;
                restart_result = DRV_UART_DMA_Recv_Start(uart, rx_buffers[ch], RX_BUFFER_SIZE);
            }
            
            if (restart_result == 0) {
                channel_rx_active[ch] = true;
            }
        }
    }
}

/******************************************************************************
* Print Parser Statistics
******************************************************************************/
static void print_parser_statistics(void)
{
    parser_stats_t stats;
    message_parser_get_stats(&stats);
    
    DEMO_Debug(("\r\n=== Parser Statistics ===\r\n"));
    DEMO_Debug(("Total Messages Parsed: %d\r\n", stats.total_messages_parsed));
    DEMO_Debug(("CRC Errors: %d\r\n", stats.total_crc_errors));
    DEMO_Debug(("Success Rate: %d%%\r\n", stats.success_rate));
    DEMO_Debug(("Messages in Progress: %d\r\n", stats.messages_in_progress));
    DEMO_Debug(("========================\r\n\r\n"));
}

/******************************************************************************
* Message Parser Demo Main Function
******************************************************************************/
int message_parser_demo_main(void)
{
    /* Initialize system */
    sysclk_init();
    board_init();
    
    /* Enable XDMAC clock */
    pmc_enable_periph_clk(ID_XDMAC);
    
    /* Initialize all USART/UART channels */
    uint32_t baudrate = 115200;
    
    DRV_USART_Comm_Init(USART0, baudrate);
    DRV_USART_Comm_Init(USART1, baudrate);
    DRV_USART_Comm_Init(USART2, baudrate);
    DRV_UART_Comm_Init(UART0, baudrate);
    DRV_UART_Comm_Init(UART1, baudrate);
    DRV_UART_Comm_Init(UART2, baudrate);
    DRV_UART_Comm_Init(UART3, baudrate);
    DRV_UART_Comm_Init(UART4, baudrate);
    
    /* Initialize message parser */
    message_parser_init();
    
    DEMO_Debug(("=== Message Parser Demo Started ===\r\n"));
    DEMO_Debug(("Protocol: [SENSOR_ID][LENGTH][DATA][CRC]\r\n"));
    DEMO_Debug(("Sensors: 1=Temp, 2=Humidity, 3=Pressure, 4=Light, 5=Motion, 6=Sound\r\n"));
    DEMO_Debug(("Channels: USART0-2, UART0-4 (8 total)\r\n\r\n"));
    
    uint32_t demo_cycle = 0;
    
    while (1) {
        ioport_toggle_pin_level(LED_0_PIN);
        
        DEMO_Debug(("=== Demo Cycle %d ===\r\n", ++demo_cycle));
        
        /* Start receive operations on all channels */
        start_receive_operations();
        
        /* Send test messages */
        send_test_messages();
        
        /* Wait for operations to complete while doing other work */
        uint32_t cpu_tasks = 0;
        uint32_t timeout = 100000; // Prevent infinite loop
        
        while (timeout-- > 0) {
            /* Check for received messages */
            check_received_messages();
            
            /* CPU can do other productive work */
            volatile uint32_t calculation = 0;
            for (int i = 0; i < 50; i++) {
                calculation += i * i;
            }
            cpu_tasks++;
            
            /* Check if all operations are idle */
            bool any_active = false;
            for (int ch = 0; ch < MAX_CHANNELS; ch++) {
                if (channel_rx_active[ch]) {
                    any_active = true;
                    break;
                }
            }
            
            if (!any_active && cpu_tasks > 1000) {
                break; // All operations completed
            }
        }
        
        DEMO_Debug(("CPU performed %d tasks during DMA operations\r\n", cpu_tasks));
        
        /* Print statistics every few cycles */
        if (demo_cycle % 3 == 0) {
            print_parser_statistics();
        }
        
        /* Delay between demo cycles */
        delay_ms(2000);
    }
    
    return 0;
}

/* End of File */