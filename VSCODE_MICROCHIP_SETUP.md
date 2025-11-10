# SAME70-XPLD VS Code + Microchip Studio 개발환경 가이드

## 개요
이 설정은 VS Code에서 코드 편집과 빌드를 하고, Microchip Studio에서 디버깅을 하는 하이브리드 방식입니다.

## 설정 완료 사항

### 1. 빌드 환경
- ✅ **툴체인**: Atmel Studio 7.0의 ARM GCC 사용
- ✅ **빌드 시스템**: PowerShell 빌드 스크립트
- ✅ **IntelliSense**: VS Code C/C++ 확장 설정 완료

### 2. 개발 워크플로우

#### A. VS Code에서 개발하기
1. **코드 편집**: VS Code에서 모든 소스 파일 편집
2. **빌드**: `Ctrl+Shift+B` 또는 `F1` → "Tasks: Run Task" → "Build"
3. **오류 확인**: Problems 패널에서 컴파일 오류 확인

#### B. Microchip Studio에서 디버깅하기
1. **Microchip Studio 7.0 실행**
2. **기존 프로젝트 열기**: 
   - File → Open → Project/Solution
   - `AS70_SAME70_XPLD_348_USART_XDMAC.atsln` 파일 선택
3. **디버깅 시작**:
   - 보드 연결 확인 (EDBG USB 연결)
   - F5 키 또는 Debug → Start Debugging and Break
   - 자동으로 플래시하고 디버깅 시작

### 3. 빌드 경로 설정
- **ELF 파일**: `Debug/AS70_SAME70_XPLD_348_USART_XDMAC.elf`
- **HEX 파일**: `Debug/AS70_SAME70_XPLD_348_USART_XDMAC.hex`
- **빌드 출력**: `Debug/` 폴더

### 4. VS Code 전용 빌드 명령어

#### PowerShell에서:
```powershell
# 프로젝트 빌드
.\build.ps1

# 클린 빌드
.\build.ps1 clean
.\build.ps1

# 빌드 결과 확인
dir Debug\*.elf
dir Debug\*.hex
```

#### VS Code Tasks:
- **빌드**: `Ctrl+Shift+B`
- **클린**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Clean"
- **리빌드**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Rebuild"

### 5. 디버깅 옵션

#### 옵션 1: Microchip Studio 디버깅 (권장)
- **장점**: 완전한 하드웨어 지원, 레지스터 뷰, 메모리 뷰
- **단점**: IDE 전환 필요

#### 옵션 2: VS Code Cortex-Debug (고급 사용자)
- **필요사항**: 
  - Cortex-Debug 확장 설치
  - OpenOCD 또는 J-Link 설치
  - 추가 설정 필요
- **사용법**: F5 키로 시작

### 6. 개발 팁

#### VS Code에서 효율적인 개발:
1. **IntelliSense 활용**: 자동완성과 오류 표시 활용
2. **Git 연동**: Source Control 패널 사용
3. **Extensions 활용**:
   - C/C++ (Microsoft)
   - Makefile Tools
   - GitLens
   - Better Comments

#### 파일 동기화:
VS Code에서 파일을 수정하면 Microchip Studio에서 자동으로 변경사항을 감지합니다.
"File has been modified externally" 다이얼로그가 나타나면 "Yes to All"을 클릭하세요.

### 7. 문제 해결

#### 빌드 문제:
```powershell
# 툴체인 경로 확인
Test-Path "C:\Program Files (x86)\Atmel\Studio\7.0\toolchain\arm\arm-gnu-toolchain\bin\arm-none-eabi-gcc.exe"

# 수동 빌드 테스트
& "C:\Program Files (x86)\Atmel\Studio\7.0\toolchain\arm\arm-gnu-toolchain\bin\arm-none-eabi-gcc.exe" --version
```

#### IntelliSense 문제:
1. `Ctrl+Shift+P` → "C/C++: Reload IntelliSense"
2. `.vscode/c_cpp_properties.json` 확인
3. 컴파일러 경로가 올바른지 확인

#### Microchip Studio 디버깅 문제:
1. **보드 연결 확인**: EDBG USB 포트 사용
2. **드라이버 확인**: Device Manager에서 EDBG 장치 확인
3. **프로젝트 설정**: Tools → Device Programming에서 디바이스 확인

### 8. 고급 VS Code 디버깅 설정

만약 VS Code에서 직접 디버깅을 원한다면:

1. **Cortex-Debug 확장 설치**
2. **OpenOCD 설치** (별도 설치 필요)
3. **SVD 파일 다운로드** (ATSAME70Q21.svd)

### 9. 권장 개발 환경

```
┌─────────────────┐    ┌──────────────────────┐
│   VS Code       │    │  Microchip Studio    │
│                 │    │                      │
│ ▪ 코드 편집     │◄──►│ ▪ 디버깅             │
│ ▪ 빌드          │    │ ▪ 플래시 프로그래밍  │
│ ▪ Git 관리      │    │ ▪ 레지스터 뷰        │
│ ▪ IntelliSense  │    │ ▪ 메모리 뷰          │
└─────────────────┘    └──────────────────────┘
```

---

## 빠른 시작

1. **VS Code에서 코드 수정**
2. **VS Code에서 빌드** (`Ctrl+Shift+B`)
3. **Microchip Studio 실행 후 디버깅** (F5)

이제 VS Code의 강력한 편집 기능과 Microchip Studio의 완벽한 디버깅 환경을 모두 활용할 수 있습니다!