# SAME70 Non-Blocking DMA Implementation

## 개요
이 프로젝트는 ATSAME70Q21 마이크로컨트롤러에서 USART/UART의 DMA 전송을 blocking 방식에서 **non-blocking 방식**으로 개선한 구현입니다.

## 주요 개선사항

### 1. Non-Blocking DMA API 추가
기존의 blocking DMA 함수들과 함께 새로운 non-blocking API들을 제공합니다:

#### USART Non-Blocking Functions
```c
uint32_t DRV_USART_DMA_Send_Start(Usart *phandle, void *pbuf, uint32_t size);
uint32_t DRV_USART_DMA_Send_IsComplete(Usart *phandle);
uint32_t DRV_USART_DMA_Send_Abort(Usart *phandle);

uint32_t DRV_USART_DMA_Recv_Start(Usart *phandle, void *pbuf, uint32_t size);
uint32_t DRV_USART_DMA_Recv_IsComplete(Usart *phandle);
uint32_t DRV_USART_DMA_Recv_Abort(Usart *phandle);
```

#### UART Non-Blocking Functions
```c
uint32_t DRV_UART_DMA_Send_Start(Uart *phandle, void *pbuf, uint32_t size);
uint32_t DRV_UART_DMA_Send_IsComplete(Uart *phandle);
uint32_t DRV_UART_DMA_Send_Abort(Uart *phandle);

uint32_t DRV_UART_DMA_Recv_Start(Uart *phandle, void *pbuf, uint32_t size);
uint32_t DRV_UART_DMA_Recv_IsComplete(Uart *phandle);
uint32_t DRV_UART_DMA_Recv_Abort(Uart *phandle);
```

### 2. 상태 추적 시스템
각 DMA 채널의 상태를 추적하여 동시 전송을 안전하게 관리합니다:
```c
typedef struct {
    bool tx_active;
    bool rx_active;
    uint32_t tx_channel;
    uint32_t rx_channel;
} dma_state_t;
```

### 3. 레거시 호환성
기존 blocking 함수들(`DRV_USART_DMA_Send`, `DRV_UART_DMA_Send` 등)은 내부적으로 non-blocking 함수들을 사용하도록 리팩토링되어 기존 코드와의 호환성을 유지합니다.

## Blocking vs Non-Blocking 비교

### Blocking 방식 (기존)
```c
// CPU가 각 전송 완료까지 대기 (블로킹)
DRV_USART_DMA_Send(USART0, buffer0, size, timeout);  // CPU 대기
DRV_USART_DMA_Send(USART1, buffer1, size, timeout);  // CPU 대기
DRV_UART_DMA_Send(UART0, buffer2, size, timeout);    // CPU 대기

// 단점:
// - CPU가 각 전송마다 blocking 상태
// - 순차적 전송으로 총 시간이 길어짐
// - DMA의 장점(비동기 처리)을 활용하지 못함
```

### Non-Blocking 방식 (개선)
```c
// 모든 DMA 전송을 동시에 시작
DRV_USART_DMA_Send_Start(USART0, buffer0, size);
DRV_USART_DMA_Send_Start(USART1, buffer1, size);
DRV_UART_DMA_Send_Start(UART0, buffer2, size);

// CPU가 다른 작업 수행 가능
while (!all_transfers_complete()) {
    perform_other_cpu_tasks();  // CPU가 생산적인 작업 수행
    check_transfer_completions(); // Non-blocking 완료 확인
}

// 장점:
// - 모든 채널이 동시에 병렬 전송
// - CPU가 전송 중에 다른 작업 수행 가능
// - 전체 처리 시간 단축
// - 시스템 응답성 향상
```

## 성능 향상 효과

### 1. 처리 시간 단축
- **Blocking**: 8개 채널 순차 전송 = 8 × 전송시간
- **Non-Blocking**: 8개 채널 병렬 전송 = 1 × 전송시간 (최대)

### 2. CPU 활용률 개선
- **Blocking**: CPU가 대기 상태로 유휴
- **Non-Blocking**: CPU가 전송 중에 다른 작업 수행

### 3. 시스템 반응성 향상
- 인터럽트 처리, UI 응답 등이 DMA 전송에 의해 지연되지 않음

## 사용 예제

### 기본 Non-Blocking 사용법
```c
// 1. DMA 전송 시작
if (DRV_USART_DMA_Send_Start(USART0, tx_buffer, buffer_size) == 0) {
    printf("DMA transmission started\n");
    
    // 2. CPU는 다른 작업 수행
    while (!DRV_USART_DMA_Send_IsComplete(USART0)) {
        // 다른 중요한 작업들...
        process_user_input();
        update_display();
        handle_other_peripherals();
    }
    
    printf("DMA transmission completed\n");
}
```

### Non-Blocking Send + Receive 동시 처리
```c
// 송신과 수신을 동시에 시작
DRV_USART_DMA_Send_Start(USART0, tx_buffer, tx_size);
DRV_USART_DMA_Recv_Start(USART0, rx_buffer, rx_size);

// 둘 다 완료될 때까지 다른 작업 수행
while (!DRV_USART_DMA_Send_IsComplete(USART0) || 
       !DRV_USART_DMA_Recv_IsComplete(USART0)) {
    // CPU가 다른 중요한 작업 수행
    perform_background_tasks();
}

printf("Both TX and RX completed!\n");
```

### 다중 채널 병렬 Send + Receive
```c
// 모든 8개 채널에서 송신과 수신을 동시에 시작
DRV_USART_DMA_Send_Start(USART0, tx_buf0, size);
DRV_USART_DMA_Recv_Start(USART0, rx_buf0, 1);
DRV_USART_DMA_Send_Start(USART1, tx_buf1, size);
DRV_USART_DMA_Recv_Start(USART1, rx_buf1, 1);
// ... USART2, UART0-4 동일하게 처리

printf("16 DMA operations (8 TX + 8 RX) started!\n");

// 모든 전송이 완료될 때까지 CPU는 다른 작업 수행
uint32_t cpu_tasks = 0;
while (/* check all completions */) {
    // CPU 생산적 작업
    perform_calculations();
    cpu_tasks++;
    
    // 완료 상태 확인 및 수신 데이터 처리
    if (DRV_USART_DMA_Recv_IsComplete(USART0)) {
        process_received_data(rx_buf0);
    }
    // ... 다른 채널들도 동일하게 처리
}

printf("All operations complete! CPU did %d tasks\n", cpu_tasks);
```

## 파일 구조

### 수정된 파일들
- `src/drv_usart_xdmac.h` - USART non-blocking API 선언
- `src/drv_usart_xdmac.c` - USART non-blocking 구현
- `src/drv_uart_xdmac.h` - UART non-blocking API 선언  
- `src/drv_uart_xdmac.c` - UART non-blocking 구현
- `src/main_usart_xdmac.c` - blocking vs non-blocking 데모

### 새로 추가된 파일들
- `src/main_nonblocking_demo.c` - 종합적인 성능 비교 데모

## 데모 실행

### 1. 종합 데모 (main_usart_xdmac.c)
**Blocking Mode:**
- USART0, UART0에서 순차적 Send + Recv 처리
- CPU가 각 DMA 작업마다 대기 (blocking)

**Non-blocking Mode:**
- 모든 8개 채널에서 동시 Send + Recv 시작 (총 16개 DMA 작업)
- CPU가 DMA 작업 중에 생산적인 계산 수행
- 실시간으로 완료 상태 모니터링 및 수신 데이터 처리
- CPU 작업량과 DMA 완료 개수 표시

**데모 특징:**
```
BLOCKING MODE:
  - 2개 채널 순차 처리 (TX → RX → TX → RX)
  - CPU 대기 시간: 높음
  - 총 처리 시간: 길음

NON-BLOCKING MODE:
  - 16개 DMA 작업 동시 실행 (8×TX + 8×RX)
  - CPU 대기 시간: 0 (계속 작업 수행)
  - 총 처리 시간: 짧음
  - CPU 활용률: 최대
```

### 2. 고급 성능 분석 데모 (main_nonblocking_demo.c)
- 정밀한 성능 측정 및 비교 분석
- 상세한 타이밍 정보와 CPU 효율성 지표
- 다양한 시나리오별 벤치마크

## 빌드 및 실행

```bash
# 빌드
powershell -ExecutionPolicy Bypass -File build.ps1

# 플래시
# (Atmel Studio의 atprogram 사용)
```

## 기술적 세부사항

### 1. 상태 관리
- 각 채널별 독립적인 DMA 상태 추적
- 중복 전송 방지 및 안전한 동시 접근 보장

### 2. 인터럽트 처리
- 기존 XDMAC 인터럽트 핸들러와 완전 호환
- 채널별 완료 플래그를 통한 상태 확인

### 3. 메모리 관리
- 정적 상태 배열로 최소한의 메모리 사용
- 동적 할당 없이 효율적인 구조

## 결론
이 non-blocking DMA 구현을 통해:
- **성능 향상**: 병렬 전송으로 처리 시간 단축
- **효율성 개선**: CPU 활용도 극대화
- **반응성 향상**: 시스템 전체 응답성 개선
- **호환성 유지**: 기존 코드 수정 없이 사용 가능

DMA의 진정한 장점인 비동기 처리를 최대한 활용하여 더 효율적이고 반응성 좋은 시스템을 구현할 수 있습니다.