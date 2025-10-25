# IntelliSense 문제 해결 가이드

## 문제 상황
- Ctrl+클릭으로 함수 정의로 이동이 안 됨
- IntelliSense가 제대로 작동하지 않음
- 원인: ARM GCC 툴체인이 설치되지 않았거나 PATH에 없음

## 해결 방법

### 1. ARM GNU Toolchain 설치 (권장)

#### 자동 설치 (Chocolatey):
```powershell
# 관리자 권한으로 PowerShell 실행 후
choco install gcc-arm-embedded

# 설치 후 확인
arm-none-eabi-gcc --version
```

#### 수동 설치:
1. https://developer.arm.com/downloads/-/gnu-rm 접속
2. "GNU Arm Embedded Toolchain" 다운로드
3. 설치 시 "Add path to environment variable" 체크
4. VS Code 재시작

### 2. c_cpp_properties.json 업데이트

설치 후 컴파일러 경로 확인:
```powershell
where arm-none-eabi-gcc
```

경로가 나오면 `.vscode/c_cpp_properties.json`에서 다음 수정:

#### 절대 경로 사용 (예시):
```json
"compilerPath": "C:\\Program Files (x86)\\GNU Arm Embedded Toolchain\\10 2021.10\\bin\\arm-none-eabi-gcc.exe"
```

#### 또는 환경 변수 사용:
```json
"compilerPath": "arm-none-eabi-gcc"
```

### 3. VS Code 재시작

1. VS Code 완전 종료
2. 다시 실행
3. C/C++ 확장이 자동으로 설정을 다시 로드

### 4. IntelliSense 강제 갱신

- `Ctrl+Shift+P` → "C/C++: Reset IntelliSense Database" 실행

## 대안: Microsoft C++ 컴파일러 사용

ARM GCC 설치가 어려운 경우 임시로 다음 설정 사용:

```json
{
    "configurations": [
        {
            "name": "SAME70",
            "includePath": [
                "${workspaceFolder}/src",
                "${workspaceFolder}/src/config",
                "${workspaceFolder}/src/ASF/**"
            ],
            "defines": [
                "__SAME70Q21__",
                "BOARD=SAME70_XPLAINED"
            ],
            "compilerPath": "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/*/bin/Hostx64/x64/cl.exe",
            "cStandard": "c99",
            "cppStandard": "c++11",
            "intelliSenseMode": "msvc-x64"
        }
    ],
    "version": 4
}
```

## 확인 방법

1. 상태 표시줄에서 "C/C++" 클릭 → 설정 정보 확인
2. 함수에 마우스 오버 시 정보 표시되는지 확인
3. Ctrl+클릭으로 정의로 이동 테스트

## 추가 팁

### IntelliSense 모드 변경:
만약 여전히 문제가 있다면 `intelliSenseMode`를 다음 중 하나로 변경:
- "gcc-arm" (기본)
- "clang-arm" 
- "msvc-x64" (Microsoft 컴파일러 사용 시)

### 포함 경로 확장:
필요 시 `includePath`에 추가:
```json
"${workspaceFolder}/src/ASF/**",
"${workspaceFolder}/**"
```

이렇게 설정하면 Ctrl+클릭으로 함수 정의로 이동할 수 있습니다.