# PC Tools for SAME70-XPLD Communication

This directory contains communication tools for interfacing with the SAME70-XPLD board from a PC.

## 🏗️ Directory Structure

```
pc_tools/
├── python/                      # 🐍 완전한 GUI 모니터링 도구 (RECOMMENDED)
│   ├── same70_gui_monitor.py   # ⭐ GUI 실시간 모니터링 도구
│   ├── same70_comm.py          # CLI 통신 라이브러리
│   ├── requirements.txt         # 의존성 패키지 목록
│   ├── launch_monitor.bat      # Windows 자동 실행 스크립트
│   └── README_GUI_Monitor.md   # GUI 도구 상세 가이드
├── csharp/          # 🔷 C#/.NET implementation  
├── nodejs/          # 🟨 Node.js implementation
├── cpp/             # 🔵 C++ implementation
└── README.md        # This file
```

## 📊 Language Comparison

### 1. 🐍 Python (★★★★★ HIGHLY RECOMMENDED)

**장점:**
- ✅ **빠른 개발**: 시리얼 통신용 `pyserial` 라이브러리 완성도 높음
- ✅ **데이터 분석**: numpy, pandas로 수신 데이터 분석 용이
- ✅ **시각화**: matplotlib, plotly로 실시간 그래프 생성
- ✅ **크로스 플랫폼**: Windows/Linux/macOS 모두 지원
- ✅ **프로토타이핑**: 빠른 테스트와 스크립트 작성
- ✅ **GUI 개발**: tkinter, PySide6로 사용자 인터페이스 구현

**단점:**
- ⚠️ 실행 속도 (임베디드 통신에는 충분)
- ⚠️ 배포 시 의존성 관리

**추천 용도:**
- 개발/테스트 도구
- 데이터 로깅 및 분석
- 프로토콜 디버깅
- 실시간 모니터링

### 2. 🔷 C#/.NET (★★★★☆)

**장점:**
- ✅ **Windows 최적화**: .NET 생태계 완성도
- ✅ **GUI 개발**: WPF, WinForms로 네이티브 Windows 앱
- ✅ **성능**: Python보다 빠른 실행 속도
- ✅ **타입 안정성**: 강타입 언어로 안정적
- ✅ **멀티스레딩**: 비동기 처리 용이

**단점:**
- ⚠️ 주로 Windows 환경 (Linux/macOS 지원 제한적)
- ⚠️ 개발 속도가 Python보다 느림

**추천 용도:**
- Windows 전용 상용 도구
- 고성능 실시간 통신
- 기업용 애플리케이션

### 3. 🟨 Node.js/JavaScript (★★★☆☆)

**장점:**
- ✅ **웹 기반**: 브라우저에서 모니터링 가능
- ✅ **실시간 통신**: Socket.IO로 웹 대시보드
- ✅ **JSON 처리**: 데이터 파싱 용이
- ✅ **이벤트 기반**: 비동기 I/O 처리

**단점:**
- ⚠️ 시리얼 통신 라이브러리 안정성 이슈
- ⚠️ 바이너리 데이터 처리 복잡
- ⚠️ 임베디드 개발자에게 생소할 수 있음

**추천 용도:**
- 웹 기반 모니터링 대시보드
- 원격 제어 시스템
- JSON 프로토콜 처리

### 4. 🔵 C++ (★★★☆☆)

**장점:**
- ✅ **최고 성능**: 가장 빠른 실행 속도
- ✅ **메모리 제어**: 정밀한 리소스 관리
- ✅ **임베디드 개발자 친숙**: 유사한 프로그래밍 패러다임
- ✅ **크로스 플랫폼**: 모든 OS 지원

**단점:**
- ⚠️ **개발 시간**: 가장 오래 걸림
- ⚠️ **복잡성**: 메모리 관리, 라이브러리 설정 복잡
- ⚠️ **디버깅**: 시리얼 통신 문제 추적 어려움

**추천 용도:**
- 고성능 실시간 시스템
- 대용량 데이터 처리
- 시스템 레벨 도구

## 🎯 프로젝트 목적별 권장사항

### 개발/디버깅 도구 (권장: Python 🐍)
```bash
cd pc_tools/python
pip install -r requirements.txt
python same70_comm.py
```

**이유:**
- 빠른 프로토타이핑
- 강력한 데이터 분석 기능
- 풍부한 시각화 라이브러리

### 상용 Windows 애플리케이션 (권장: C# 🔷)
```bash
cd pc_tools/csharp
dotnet build
dotnet run
```

**이유:**
- 네이티브 Windows GUI
- 높은 성능
- 전문적인 외관

### 웹 기반 모니터링 (권장: Node.js 🟨)
```bash
cd pc_tools/nodejs
npm install
npm start
```

**이유:**
- 브라우저에서 접근 가능
- 실시간 대시보드
- 원격 모니터링

### 고성능/실시간 시스템 (권장: C++ 🔵)
```bash
cd pc_tools/cpp
mkdir build && cd build
cmake ..
make
./SAME70CommTool
```

**이유:**
- 최고의 성능
- 정밀한 타이밍 제어
- 시스템 레벨 최적화

## 🚀 빠른 시작 (Python 추천)

### 🖥️ 멀티포트 GUI 모니터링 도구 (최신! 🔥)
```bash
cd pc_tools/python
# 6개 포트 동시 모니터링 도구
launch_multiport_monitor.bat

# 또는 수동 실행
pip install -r requirements.txt
python same70_multiport_monitor.py
```

**멀티포트 GUI 도구 주요 기능:**
- 🔌 **6개 독립적인 COM 포트 동시 연결**
- 📊 **포트별 개별 End-to-End 지연시간 측정**
- 📉 **포트별 패킷 손실률 실시간 모니터링**
- 📈 **통합 비교 차트 (모든 포트 동시 표시)**
- 📝 **포트 필터링 기능이 있는 통합 로그**
- 🎮 **포트별 독립적인 자동/수동 테스트**
- 🔄 **포트별 개별 통계 초기화**

### 🖥️ 단일포트 GUI 모니터링 도구
```bash
cd pc_tools/python
# 단일 포트 상세 모니터링
launch_monitor.bat

# 또는 수동 실행
python same70_gui_monitor.py
```

### 📟 CLI 도구 (개발자용)
```bash
cd pc_tools/python
pip install -r requirements.txt
python same70_comm.py
```

## 📡 SAME70-XPLD 연결 정보

- **인터페이스**: USB CDC (Virtual COM Port)
- **기본 포트**: Windows: COM3, Linux: /dev/ttyACM0
- **보드레이트**: 115200 bps
- **데이터 비트**: 8
- **패리티**: None  
- **스톱 비트**: 1

## �️ 사용 방법 요약

1. **PC 도구 선택**: 
   - **멀티포트 모니터링**: `pc_tools/python/launch_multiport_monitor.bat` (6개 보드 동시 테스트 🚀)
   - **단일포트 상세 분석**: `pc_tools/python/launch_monitor.bat` (1개 보드 집중 분석 🔍)
   - **CLI 도구**: `pc_tools/python/same70_comm.py` (개발자용 명령줄 도구 💻)

2. **SAME70 펌웨어**: 메인 프로젝트에서 UART/XDMAC 통신 프로그램 빌드/플래시

3. **통신 테스트**: GUI에서 COM 포트 설정 후 실시간 모니터링 시작

## �🔧 개발 우선순위

1. ✅ **1단계 완료**: Python 기본 통신 도구 개발
2. ✅ **2단계 완료**: 프로토콜 정의 및 메시지 파싱  
3. ✅ **3단계 완료**: 단일포트 GUI 인터페이스
4. ✅ **4단계 완료**: 멀티포트 GUI (6개 포트 동시 모니터링)
5. **5단계 예정**: 성능 최적화 및 고급 분석 기능

---
**현재 상태**: **멀티포트 GUI 모니터링 도구 완성!** 🎉  
6개의 SAME70 보드를 동시에 모니터링하여 성능 비교 분석이 가능합니다.