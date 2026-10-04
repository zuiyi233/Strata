@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Auxiliary\Build\vcvarsall.bat" x64 -vcvars_ver=14.44.35207 >nul
if errorlevel 1 exit /b 1
set "PATH=C:\Program Files (x86)\Windows Kits\10\bin\10.0.28000.0\x64;%PATH%"
set "PATH=%PATH:C:\msys64\mingw64\bin;=%"
set "PATH=%PATH:C:\msys64\usr\bin;=%"
rem re-configure with tests on (same build dir, incremental) and build the test target
"N:\Strata\.venv\Scripts\cmake.exe" -S "N:\Strata" -B "N:\Strata\build" -DSTRATA_BUILD_TESTS=ON || exit /b 1
"N:\Strata\.venv\Scripts\cmake.exe" --build "N:\Strata\build" --target all -j 16 || exit /b 1
cd /d "N:\Strata\build"
"N:\Strata\.venv\Scripts\ctest.exe" --output-on-failure
