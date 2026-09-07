@echo off
REM Build the GL probes as native x64 using the MSVC 14.44 BuildTools that are
REM already installed on this machine. No toolchain download is required.
REM
REM 32-bit and 64-bit objects, import libraries and runtimes are never mixed:
REM this script only ever produces x64, into *64.exe names.
set VC=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat
call "%VC%" >nul 2>&1
if errorlevel 1 (echo VCVARS FAILED & exit /b 1)

echo === cl identity ===
cl 2>&1 | findstr /C:"Version"

cd /d "%~dp0"
cl /nologo /W4 /Fe:glabi64.exe  glabi.c  opengl32.lib gdi32.lib user32.lib /link /SUBSYSTEM:CONSOLE
if errorlevel 1 (echo BUILD glabi64 FAILED & exit /b 1)
cl /nologo /W4 /Fe:glchar64.exe glchar.c opengl32.lib gdi32.lib user32.lib /link /SUBSYSTEM:CONSOLE
if errorlevel 1 (echo BUILD glchar64 FAILED & exit /b 1)
echo === BUILD OK ===
