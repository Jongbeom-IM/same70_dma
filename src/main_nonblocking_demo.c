/******************************************************************************
* Non-blocking DMA Demo - Shows the advantages of non-blocking DMA
*
* This demo demonstrates:
* 1. Concurrent DMA operations on multiple channels
* 2. CPU freed for other tasks while DMA operates in background
* 3. Performance comparison between blocking vs non-blocking approaches
******************************************************************************/

#include <asf.h>
#include "drv_usart_xdmac.h"
#include "drv_uart_xdmac.h"
#include "drv_usart.h"
#include "delay.h"

/* Simple timing counter for demo purposes */
static volatile uint32_t demo_tick_counter = 0;

#ifdef DEBUG
#include <stdio.h>
#define DEMO_Debug(x)    printf x
#define DEMO_DebugError(x) printf x
#else
#define DEMO_Debug(x)
#define DEMO_DebugError(x)
#endif

/******************************************************************************
* Multi-Channel DMA State Management
******************************************************************************/
typedef struct {
	bool tx_active;
	bool rx_active;
	uint32_t tx_start_time;
	uint32_t rx_start_time;
	uint32_t tx_complete_time;
	uint32_t rx_complete_time;
} channel_state_t;

static channel_state_t usart_states[3] = {0};  // USART0-2
static channel_state_t uart_states[5] = {0};   // UART0-4

/******************************************************************************
* Performance Counters
******************************************************************************/
static uint32_t cpu_task_counter = 0;
static uint32_t background_tasks_done = 0;

/******************************************************************************
* Test Data Buffers
******************************************************************************/
static uint8_t usart0_tx_buf[] = "USART0-NonBlocking-DMA-Test\r\n";
static uint8_t usart1_tx_buf[] = "USART1-NonBlocking-DMA-Test\r\n";
static uint8_t usart2_tx_buf[] = "USART2-NonBlocking-DMA-Test\r\n";
static uint8_t uart0_tx_buf[] = "UART0-NonBlocking-DMA-Test\r\n";
static uint8_t uart1_tx_buf[] = "UART1-NonBlocking-DMA-Test\r\n";
static uint8_t uart2_tx_buf[] = "UART2-NonBlocking-DMA-Test\r\n";
static uint8_t uart3_tx_buf[] = "UART3-NonBlocking-DMA-Test\r\n";
static uint8_t uart4_tx_buf[] = "UART4-NonBlocking-DMA-Test\r\n";

static uint8_t usart0_rx_buf[10];
static uint8_t usart1_rx_buf[10];
static uint8_t usart2_rx_buf[10];
static uint8_t uart0_rx_buf[10];
static uint8_t uart1_rx_buf[10];
static uint8_t uart2_rx_buf[10];
static uint8_t uart3_rx_buf[10];
static uint8_t uart4_rx_buf[10];

/******************************************************************************
* CPU Background Tasks - Show that CPU is free while DMA operates
******************************************************************************/
void perform_cpu_intensive_task(void)
{
	volatile uint32_t calculation = 0;
	
	/* Simulate CPU-intensive work that can be done while DMA runs */
	for (int i = 0; i < 1000; i++) {
		calculation += i * i;
		calculation = calculation % 0xFFFF;
	}
	
	cpu_task_counter++;
	
	/* Blink LED to show CPU activity */
	if (cpu_task_counter % 100 == 0) {
		ioport_toggle_pin_level(LED_0_PIN);
		background_tasks_done++;
	}
}

/******************************************************************************
* Start All DMA Transmissions Concurrently (Non-blocking)
******************************************************************************/
void start_all_dma_transmissions(void)
{
	uint32_t current_time = demo_tick_counter++;
	
	DEMO_Debug(("=== Starting Concurrent DMA Transmissions ===\r\n"));
	
	/* Start all USART transmissions */
	if (DRV_USART_DMA_Send_Start(USART0, usart0_tx_buf, sizeof(usart0_tx_buf)) == 0) {
		usart_states[0].tx_active = true;
		usart_states[0].tx_start_time = current_time;
		DEMO_Debug(("USART0 TX started\r\n"));
	}
	
	if (DRV_USART_DMA_Send_Start(USART1, usart1_tx_buf, sizeof(usart1_tx_buf)) == 0) {
		usart_states[1].tx_active = true;
		usart_states[1].tx_start_time = current_time;
		DEMO_Debug(("USART1 TX started\r\n"));
	}
	
	if (DRV_USART_DMA_Send_Start(USART2, usart2_tx_buf, sizeof(usart2_tx_buf)) == 0) {
		usart_states[2].tx_active = true;
		usart_states[2].tx_start_time = current_time;
		DEMO_Debug(("USART2 TX started\r\n"));
	}
	
	/* Start all UART transmissions */
	if (DRV_UART_DMA_Send_Start(UART0, uart0_tx_buf, sizeof(uart0_tx_buf)) == 0) {
		uart_states[0].tx_active = true;
		uart_states[0].tx_start_time = current_time;
		DEMO_Debug(("UART0 TX started\r\n"));
	}
	
	if (DRV_UART_DMA_Send_Start(UART1, uart1_tx_buf, sizeof(uart1_tx_buf)) == 0) {
		uart_states[1].tx_active = true;
		uart_states[1].tx_start_time = current_time;
		DEMO_Debug(("UART1 TX started\r\n"));
	}
	
	if (DRV_UART_DMA_Send_Start(UART2, uart2_tx_buf, sizeof(uart2_tx_buf)) == 0) {
		uart_states[2].tx_active = true;
		uart_states[2].tx_start_time = current_time;
		DEMO_Debug(("UART2 TX started\r\n"));
	}
	
	if (DRV_UART_DMA_Send_Start(UART3, uart3_tx_buf, sizeof(uart3_tx_buf)) == 0) {
		uart_states[3].tx_active = true;
		uart_states[3].tx_start_time = current_time;
		DEMO_Debug(("UART3 TX started\r\n"));
	}
	
	if (DRV_UART_DMA_Send_Start(UART4, uart4_tx_buf, sizeof(uart4_tx_buf)) == 0) {
		uart_states[4].tx_active = true;
		uart_states[4].tx_start_time = current_time;
		DEMO_Debug(("UART4 TX started\r\n"));
	}
	
	DEMO_Debug(("All DMA transmissions started - CPU is now FREE!\r\n"));
}

/******************************************************************************
* Check and Handle Completed DMA Transmissions
******************************************************************************/
void check_dma_completions(void)
{
	uint32_t current_time = demo_tick_counter++;
	
	/* Check USART completions */
	for (int i = 0; i < 3; i++) {
		if (usart_states[i].tx_active) {
			if (DRV_USART_DMA_Send_IsComplete((i == 0) ? USART0 : (i == 1) ? USART1 : USART2)) {
				usart_states[i].tx_active = false;
				usart_states[i].tx_complete_time = current_time;
				uint32_t duration = current_time - usart_states[i].tx_start_time;
				DEMO_Debug(("USART%d TX completed in %d ticks\r\n", i, duration));
			}
		}
	}
	
	/* Check UART completions */
	for (int i = 0; i < 5; i++) {
		if (uart_states[i].tx_active) {
			Uart *uart_ptr = (i == 0) ? UART0 : (i == 1) ? UART1 : (i == 2) ? UART2 : (i == 3) ? UART3 : UART4;
			if (DRV_UART_DMA_Send_IsComplete(uart_ptr)) {
				uart_states[i].tx_active = false;
				uart_states[i].tx_complete_time = current_time;
				uint32_t duration = current_time - uart_states[i].tx_start_time;
				DEMO_Debug(("UART%d TX completed in %d ticks\r\n", i, duration));
			}
		}
	}
}

/******************************************************************************
* Check if All DMA Operations are Complete
******************************************************************************/
bool all_dma_complete(void)
{
	/* Check USART states */
	for (int i = 0; i < 3; i++) {
		if (usart_states[i].tx_active || usart_states[i].rx_active) {
			return false;
		}
	}
	
	/* Check UART states */
	for (int i = 0; i < 5; i++) {
		if (uart_states[i].tx_active || uart_states[i].rx_active) {
			return false;
		}
	}
	
	return true;
}

/******************************************************************************
* Performance Analysis Demo
******************************************************************************/
void performance_analysis_demo(void)
{
	uint32_t start_time, end_time;
	uint32_t initial_cpu_tasks;
	
	DEMO_Debug(("\r\n=== NON-BLOCKING DMA PERFORMANCE DEMO ===\r\n"));
	DEMO_Debug(("This demo shows CPU can do other work while DMA operates\r\n\r\n"));
	
	/* Reset counters */
	cpu_task_counter = 0;
	background_tasks_done = 0;
	initial_cpu_tasks = cpu_task_counter;
	
	/* Start all DMA operations concurrently */
	start_time = demo_tick_counter++;
	start_all_dma_transmissions();
	
	/* While DMA operates in background, CPU can do other work */
	DEMO_Debug(("CPU is now doing background tasks while DMA runs...\r\n"));
	
	while (!all_dma_complete()) {
		/* CPU does useful work while DMA operates */
		perform_cpu_intensive_task();
		
		/* Check for completions (non-blocking) */
		check_dma_completions();
	}
	
	end_time = demo_tick_counter++;
	
	/* Show performance results */
	uint32_t total_time = end_time - start_time;
	uint32_t cpu_tasks_completed = cpu_task_counter - initial_cpu_tasks;
	
	DEMO_Debug(("\r\n=== PERFORMANCE RESULTS ===\r\n"));
	DEMO_Debug(("Total time for all 8 channels: %d ticks\r\n", total_time));
	DEMO_Debug(("CPU tasks completed during DMA: %d\r\n", cpu_tasks_completed));
	DEMO_Debug(("Background processing cycles: %d\r\n", background_tasks_done));
	DEMO_Debug(("CPU utilization: PRODUCTIVE (doing other work)\r\n"));
	DEMO_Debug(("DMA channels: ALL CONCURRENT (8 channels simultaneously)\r\n"));
	DEMO_Debug(("\r\nWith blocking DMA, CPU would be BLOCKED/WAITING!\r\n"));
}

/******************************************************************************
* Comparison: Blocking vs Non-Blocking Demo
******************************************************************************/
void blocking_vs_nonblocking_comparison(void)
{
	uint32_t blocking_start, blocking_end, nonblocking_start, nonblocking_end;
	uint32_t blocking_tasks = 0, nonblocking_tasks = 0;
	
	DEMO_Debug(("\r\n=== BLOCKING vs NON-BLOCKING COMPARISON ===\r\n"));
	
	/* Test 1: Blocking approach (sequential) */
	DEMO_Debug(("Test 1: BLOCKING approach (one channel at a time)\r\n"));
	cpu_task_counter = 0;
	blocking_start = demo_tick_counter++;
	
	/* Sequential blocking operations - CPU is blocked during each */
	DRV_USART_DMA_Send(USART0, usart0_tx_buf, sizeof(usart0_tx_buf), 10000);
	DRV_USART_DMA_Send(USART1, usart1_tx_buf, sizeof(usart1_tx_buf), 10000);
	DRV_UART_DMA_Send(UART0, uart0_tx_buf, sizeof(uart0_tx_buf), 10000);
	DRV_UART_DMA_Send(UART1, uart1_tx_buf, sizeof(uart1_tx_buf), 10000);
	
	blocking_end = demo_tick_counter++;
	blocking_tasks = cpu_task_counter;
	
	/* Delay for comparison */
	delay_ms(100);
	
	/* Test 2: Non-blocking approach (concurrent) */
	DEMO_Debug(("Test 2: NON-BLOCKING approach (all channels simultaneously)\r\n"));
	cpu_task_counter = 0;
	nonblocking_start = demo_tick_counter++;
	
	/* Start all transfers concurrently */
	DRV_USART_DMA_Send_Start(USART0, usart0_tx_buf, sizeof(usart0_tx_buf));
	DRV_USART_DMA_Send_Start(USART1, usart1_tx_buf, sizeof(usart1_tx_buf));
	DRV_UART_DMA_Send_Start(UART0, uart0_tx_buf, sizeof(uart0_tx_buf));
	DRV_UART_DMA_Send_Start(UART1, uart1_tx_buf, sizeof(uart1_tx_buf));
	
	/* CPU can do work while transfers happen */
	while (!DRV_USART_DMA_Send_IsComplete(USART0) || 
	       !DRV_USART_DMA_Send_IsComplete(USART1) ||
	       !DRV_UART_DMA_Send_IsComplete(UART0) ||
	       !DRV_UART_DMA_Send_IsComplete(UART1)) {
		perform_cpu_intensive_task();
	}
	
	nonblocking_end = demo_tick_counter++;
	nonblocking_tasks = cpu_task_counter;
	
	/* Show comparison results */
	DEMO_Debug(("\r\n=== COMPARISON RESULTS ===\r\n"));
	DEMO_Debug(("BLOCKING approach:\r\n"));
	DEMO_Debug(("  Time: %d ticks\r\n", blocking_end - blocking_start));
	DEMO_Debug(("  CPU tasks done: %d (CPU was blocked!)\r\n", blocking_tasks));
	DEMO_Debug(("  Channels: Sequential (one at a time)\r\n"));
	
	DEMO_Debug(("NON-BLOCKING approach:\r\n"));
	DEMO_Debug(("  Time: %d ticks\r\n", nonblocking_end - nonblocking_start));
	DEMO_Debug(("  CPU tasks done: %d (CPU was productive!)\r\n", nonblocking_tasks));
	DEMO_Debug(("  Channels: Concurrent (all simultaneously)\r\n"));
	
	DEMO_Debug(("\r\nNON-BLOCKING ADVANTAGES:\r\n"));
	DEMO_Debug(("  - CPU can do other work while DMA runs\r\n"));
	DEMO_Debug(("  - Multiple channels operate concurrently\r\n"));
	DEMO_Debug(("  - Better system responsiveness\r\n"));
	DEMO_Debug(("  - Higher overall throughput\r\n"));
}

/******************************************************************************
* Main Demo Function
******************************************************************************/
int nonblocking_demo_main(void)
{
	/* Initialize system */
	sysclk_init();
	board_init();
	
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
	
	DEMO_Debug(("=== NON-BLOCKING DMA DEMONSTRATION ===\r\n"));
	DEMO_Debug(("All 8 channels (USART0-2, UART0-4) initialized\r\n\r\n"));
	
	while (1) {
		/* Run performance analysis demo */
		performance_analysis_demo();
		
		delay_ms(2000);
		
		/* Run blocking vs non-blocking comparison */
		blocking_vs_nonblocking_comparison();
		
		delay_ms(5000);
		
		DEMO_Debug(("\r\n--- Repeating demo in 3 seconds ---\r\n\r\n"));
		delay_ms(3000);
	}
	
	return 0;
}