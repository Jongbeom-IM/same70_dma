# 메시지 파서 (Message Parser) 사용 가이드

## 📋 메시지 프로토콜 구조

### 프로토콜 형식
```
[SENSOR_ID(1바이트)] [LENGTH(1바이트)] [DATA(N바이트)] [CRC(1바이트)]
```

### 필드 설명
- **SENSOR_ID**: 센서 식별자 (0x01~0x06)
- **LENGTH**: 데이터 길이 (0~64바이트)  
- **DATA**: 실제 센서 데이터 (가변 길이)
- **CRC**: 데이터 무결성 검사 (XOR 체크섬)

## 🔍 지원 센서 타입

| 센서 ID | 센서 타입 | 설명 |
|---------|----------|------|
| 0x01 | Temperature | 온도 센서 |
| 0x02 | Humidity | 습도 센서 |
| 0x03 | Pressure | 압력 센서 |
| 0x04 | Light | 조도 센서 |
| 0x05 | Motion | 모션 센서 |
| 0x06 | Sound | 음향 센서 |

## 💡 사용 예제

### 1. 파서 초기화
```c
#include "message_parser.h"

// 파서 초기화 (8개 채널 지원)
message_parser_init();
```

### 2. 메시지 생성
```c
uint8_t sensor_data[] = {25, 5}; // 25.5°C
uint8_t message_buffer[MAX_MESSAGE_SIZE];

// 온도 센서 메시지 생성
uint8_t msg_length = message_parser_create_message(
    SENSOR_TEMPERATURE,  // 센서 ID
    sensor_data,         // 데이터
    2,                   // 데이터 길이
    message_buffer       // 출력 버퍼
);

// 결과: [0x01][0x02][0x19][0x05][CRC]
```

### 3. 메시지 파싱
```c
// 수신된 데이터를 파싱
message_parse_result_t result = message_parser_process(
    channel_id,     // 채널 ID (0-7)
    rx_buffer,      // 수신 버퍼
    rx_length       // 수신 길이
);

switch (result) {
    case MSG_PARSE_COMPLETE:
        // 메시지 파싱 완료
        parsed_message_t message;
        if (message_parser_get_message(channel_id, &message)) {
            printf("Sensor: %s, Data: %d bytes\n", 
                   message_parser_get_sensor_name(message.sensor_id),
                   message.data_length);
        }
        break;
        
    case MSG_PARSE_CRC_ERROR:
        printf("CRC 오류!\n");
        break;
        
    case MSG_PARSE_INCOMPLETE:
        printf("데이터 더 필요\n");
        break;
}
```

## 🚀 Non-Blocking DMA와 연동

### 완전한 Non-Blocking 메시지 처리
```c
// 1. 모든 채널에서 동시 수신 시작
for (int ch = 0; ch < 8; ch++) {
    DRV_USART_DMA_Recv_Start(usart[ch], rx_buf[ch], MAX_MESSAGE_SIZE);
}

// 2. CPU는 다른 작업 수행하면서 수신 확인
while (active_channels > 0) {
    for (int ch = 0; ch < 8; ch++) {
        if (DRV_USART_DMA_Recv_IsComplete(usart[ch])) {
            // 3. 수신 완료된 채널에서 메시지 파싱
            message_parse_result_t result = message_parser_process(
                ch, rx_buf[ch], received_length);
                
            if (result == MSG_PARSE_COMPLETE) {
                // 4. 파싱된 메시지 처리
                parsed_message_t msg;
                message_parser_get_message(ch, &msg);
                process_sensor_data(&msg);
            }
            
            // 5. 다음 수신을 위해 재시작
            DRV_USART_DMA_Recv_Start(usart[ch], rx_buf[ch], MAX_MESSAGE_SIZE);
        }
    }
    
    // CPU는 DMA 동작 중에 다른 작업 수행
    perform_background_tasks();
}
```

## 📊 실제 메시지 예제

### 온도 센서 메시지 (25.5°C)
```
Raw: [0x01][0x02][0x19][0x05][0x1C]
- Sensor ID: 0x01 (Temperature)
- Length: 0x02 (2 bytes)
- Data: 0x19 0x05 (25, 5 → 25.5°C)
- CRC: 0x1C (checksum)
```

### 모션 센서 메시지 (감지됨)
```
Raw: [0x05][0x01][0x01][0x05]
- Sensor ID: 0x05 (Motion)
- Length: 0x01 (1 byte)
- Data: 0x01 (Motion detected)
- CRC: 0x05 (checksum)
```

### 빈 메시지 (하트비트)
```
Raw: [0x01][0x00][0x01]
- Sensor ID: 0x01 (Temperature)
- Length: 0x00 (no data)
- Data: (none)
- CRC: 0x01 (checksum)
```

## 📈 성능 통계

### 파서 통계 확인
```c
parser_stats_t stats;
message_parser_get_stats(&stats);

printf("총 파싱된 메시지: %d\n", stats.total_messages_parsed);
printf("CRC 오류: %d\n", stats.total_crc_errors);
printf("성공률: %d%%\n", stats.success_rate);
printf("처리 중인 메시지: %d\n", stats.messages_in_progress);
```

## 🔧 고급 기능

### 1. 채널별 파서 리셋
```c
// 특정 채널의 파서 상태 초기화
message_parser_reset_channel(channel_id);
```

### 2. 메시지 상세 출력
```c
// 파싱된 메시지를 상세히 출력
message_parser_print_message(&parsed_msg);
```

### 3. 센서 이름 조회
```c
const char* name = message_parser_get_sensor_name(SENSOR_TEMPERATURE);
printf("센서: %s\n", name); // "Temperature"
```

## 🎯 장점 및 특징

### ✅ **견고성**
- CRC 체크섬으로 데이터 무결성 보장
- 잘못된 메시지 자동 복구
- 채널별 독립적 상태 관리

### ⚡ **성능**
- Non-blocking 방식으로 CPU 효율성 최대화
- 8개 채널 동시 메시지 처리
- 최소한의 메모리 사용 (정적 할당)

### 🔄 **유연성**
- 가변 길이 데이터 지원 (0~64바이트)
- 6가지 센서 타입 확장 가능
- 실시간 통계 및 모니터링

### 🛡️ **안정성**
- 파싱 오류 시 자동 복구
- 타임아웃 방지 메커니즘
- 채널별 독립적 오류 처리

이 메시지 파서를 통해 **구조화된 센서 데이터**를 **안정적이고 효율적으로** 처리할 수 있으며, **Non-blocking DMA**와 결합하여 **최고의 성능**을 달성할 수 있습니다!