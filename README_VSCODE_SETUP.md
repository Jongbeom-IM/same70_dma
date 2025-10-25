# SAME70 VS Code 개발환경 설정 가이드

## 설정 완료 내역

### 1. 프로젝트 정보
- **MCU**: ATSAME70Q21 (ARM Cortex-M7)
- **보드**: SAME70 Xplained Pro
- **툴체인**: ARM GCC
- **IDE**: VS Code

### 2. 생성된 설정 파일
- `.vscode/c_cpp_properties.json` - IntelliSense 설정
- `.vscode/tasks.json` - 빌드 작업 정의
- `.vscode/launch.json` - 디버그 설정 (Cortex-Debug 확장 필요)
- `Makefile` - 빌드 시스템

### 3. 필수 도구 설치

#### Windows에서 Chocolatey 사용:
```powershell
# ARM GCC Toolchain
choco install gcc-arm-embedded

# Make 도구
choco install make

# OpenOCD (디버깅용)
choco install openocd

# 설치 확인
arm-none-eabi-gcc --version
make --version
openocd --version
```

#### 수동 설치:
1. **ARM GCC Toolchain**: https://developer.arm.com/downloads/-/gnu-rm
2. **Make for Windows**: http://gnuwin32.sourceforge.net/packages/make.htm
3. **OpenOCD**: https://openocd.org/

### 4. 빌드 방법

#### VS Code에서:
1. `Ctrl+Shift+P` → "Tasks: Run Task" → "Build" 선택
2. 또는 `Ctrl+Shift+B` (빌드 단축키)

#### 터미널에서:
```powershell
# 프로젝트 디렉토리로 이동
cd "c:\Users\iammap\MPLABXProjects\AS70_SAME70_XPLD_348_USART_XDMAC"

# 빌드 실행
make

# 클린 빌드
make clean
make

# 결과 파일 확인
dir Debug\*.elf
dir Debug\*.hex
dir Debug\*.bin
```

### 5. 디버깅 설정

#### 필요한 파일:
1. **SVD 파일**: ATSAME70Q21.svd (레지스터 뷰용)
   - Microchip 웹사이트에서 다운로드
2. **OpenOCD 설정**: 이미 설정됨

#### 디버거 연결:
- SAME70 Xplained Pro 보드의 EDBG (Embedded Debugger) 사용
- USB로 PC와 연결
- VS Code에서 F5 키로 디버깅 시작

### 6. 문제 해결

#### 빌드 오류:
1. **툴체인 경로 확인**: `arm-none-eabi-gcc`가 PATH에 있는지 확인
2. **소스 파일 경로**: Makefile의 소스 파일 경로가 정확한지 확인
3. **권한 문제**: 관리자 권한으로 VS Code 실행

#### IntelliSense 문제:
1. **컴파일러 경로 확인**: c_cpp_properties.json의 compilerPath 설정
2. **포함 경로 확인**: includePath에 모든 필요한 경로가 있는지 확인

#### 디버깅 문제:
1. **Cortex-Debug 확장 설치 확인**
2. **OpenOCD 설치 및 설정 확인**
3. **하드웨어 연결 상태 확인**

### 7. 추가 기능

#### 코드 포매팅:
- C/C++ 확장의 자동 포매팅 활용
- `.clang-format` 파일로 스타일 커스터마이징

#### Git 연동:
```powershell
git init
echo "Debug/" >> .gitignore
echo ".vscode/settings.json" >> .gitignore
git add .
git commit -m "Initial VS Code setup for SAME70 project"
```

### 8. 개발 워크플로우

1. **코드 작성**: VS Code에서 소스 파일 편집
2. **빌드**: `Ctrl+Shift+B` 또는 Tasks 메뉴 사용
3. **디버깅**: F5 키로 디버깅 모드 시작
4. **플래시**: Makefile의 `make flash` 타겟 사용

---

이제 VS Code에서 SAME70 프로젝트 개발을 시작할 수 있습니다!