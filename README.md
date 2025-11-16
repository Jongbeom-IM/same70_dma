# 🚀 SAME70-XPLD DMA UART 통신 프로젝트

Atmel SAME70-XPLD 개발보드를 사용한 고성능 UART 통신 프로젝트입니다. XDMAC(Extended DMA Controller)를 활용하여 효율적인 비동기 시리얼 통신을 구현합니다.

## 📋 프로젝트 개요

- **타겟**: ATSAME70Q21 (ARM Cortex-M7, 300MHz)
- **개발환경**: Atmel Studio 7.0 + VS Code
- **주요 기능**: XDMAC 기반 논블로킹 UART 통신
- **PC 도구**: Python GUI 멀티포트 모니터링

## 🎯 핵심 특징

### 🔧 임베디드 펌웨어
- **XDMAC 최적화**: 효율적인 인터럽트 처리로 CPU 부하 최소화
- **다중 UART 지원**: 8개 채널 (USART0-2, UART0-4) 동시 사용 가능
- **Non-blocking I/O**: DMA 기반 비동기 통신으로 실시간 성능 보장
- **메시지 파서**: 구조화된 프로토콜로 안정적인 데이터 전송

### 🖥️ PC 모니터링 도구
- **멀티포트 GUI**: 최대 6개 보드 동시 모니터링 🆕
- **실시간 분석**: End-to-End 지연시간, 패킷 손실률 측정
- **시각적 대시보드**: 실시간 차트와 통계 그래프
- **비교 분석**: 여러 보드 성능 동시 비교

## 🚀 빠른 시작

### 1. 개발 환경 설정
```bash
# VS Code 디버깅 환경 (권장)
code .
# Ctrl+Shift+P -> "Tasks: Run Build Task" 선택

# 또는 PowerShell 빌드
./build.ps1
```

### 2. 펌웨어 플래시
```bash
# Atmel Studio로 디버깅/플래시
# 또는 OpenOCD 사용
```

### 3. PC 모니터링 도구 실행

#### 🔥 멀티포트 모니터링 (6개 보드 동시)
```bash
cd pc_tools/python
launch_multiport_monitor.bat
```

#### 🔍 단일포트 상세 분석
```bash
cd pc_tools/python  
launch_monitor.bat
```

## 📊 성능 지표

### XDMAC 최적화 효과
- **인터럽트 처리 시간**: ~85% 감소 (폴링 → 비트스캔)
- **CPU 사용률**: 대폭 감소 (백그라운드 DMA 처리)
- **응답 지연시간**: 1-5ms (일반적)

### 멀티포트 동시 처리
- **최대 동시 연결**: 6개 포트
- **실시간 모니터링**: 0.1초 갱신 주기
- **데이터 처리량**: 포트당 최대 115200 bps

## 🗂️ 프로젝트 구조

```
same70_dma/
├── src/                           # 임베디드 소스코드
│   ├── main_usart_xdmac.c        # 메인 애플리케이션
│   ├── drv_usart_xdmac.c/h       # UART+XDMAC 드라이버
│   ├── drv_xdmac_handler.c/h     # 최적화된 XDMAC 인터럽트 핸들러
│   └── ASF/                       # Atmel Software Framework
├── pc_tools/                      # PC 통신 도구
│   └── python/                    
│       ├── same70_multiport_monitor.py  # 🆕 멀티포트 GUI
│       ├── same70_gui_monitor.py        # 단일포트 GUI  
│       ├── same70_comm.py               # CLI 도구
│       └── MULTIPORT_GUIDE.md           # 멀티포트 사용 가이드
├── .vscode/                       # VS Code 설정
│   ├── launch.json               # 디버깅 설정
│   └── tasks.json                # 빌드 작업
└── docs/                         # 기술 문서
```

## 📚 상세 문서

| 문서 | 내용 |
|------|------|
| [VS Code 설정 가이드](README_VSCODE_SETUP.md) | 개발 환경 구축 방법 |
| [Non-blocking DMA 구현](README_NonBlocking_DMA.md) | XDMAC 최적화 기술 상세 |
| [메시지 파서 구조](README_Message_Parser.md) | 통신 프로토콜 설계 |
| [멀티포트 모니터링 가이드](pc_tools/python/MULTIPORT_GUIDE.md) | GUI 도구 사용법 |
| [PC 도구 개요](pc_tools/README.md) | 개발 언어별 비교 분석 |

## 🔧 UART 채널 정보

SAME70Q21은 총 8개의 UART/USART 채널을 제공합니다:

| 채널 | 타입 | 핀 위치 | 용도 |
|------|------|---------|------|
| USART0 | USART | PB0/PB1 | 다목적 통신 |
| USART1 | USART | PA21/PB4 | 다목적 통신 |
| USART2 | USART | PD15/PD16 | 다목적 통신 |
| UART0 | UART | PA9/PA10 | 기본 시리얼 |
| UART1 | UART | PA5/PA6 | 기본 시리얼 |
| UART2 | UART | PD25/PD26 | 기본 시리얼 |
| UART3 | UART | PD28/PD30 | 기본 시리얼 |
| UART4 | UART | PD18/PD19 | 기본 시리얼 |

## 🏆 주요 성과

### ✅ 완료된 기능
- [x] VS Code 디버깅 환경 구축
- [x] XDMAC 인터럽트 핸들러 최적화  
- [x] 비동기 UART 드라이버 개발
- [x] 단일포트 GUI 모니터링 도구
- [x] **멀티포트 GUI 모니터링 도구 (6개 동시)** 🆕
- [x] 실시간 성능 분석 및 시각화
- [x] 메시지 파싱 프로토콜

### 🔄 진행 중
- [ ] 고급 프로토콜 기능 (패킷 분할, 재전송)
- [ ] 웹 기반 모니터링 인터페이스
- [ ] 자동화된 성능 테스트 스위트

## 🤝 기여 방법

1. 이슈 리포트: GitHub Issues 사용
2. 기능 제안: Pull Request로 제출  
3. 문서 개선: README 파일들 업데이트

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

---

**⭐ 추천 사용법**: 먼저 `pc_tools/python/launch_multiport_monitor.bat`로 멀티포트 GUI를 실행하여 여러 SAME70 보드를 동시에 테스트해보세요!