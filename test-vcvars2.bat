@echo off
echo === variant A: plain vcvars64 ===
call "C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Auxiliary\Build\vcvars64.bat"
echo errorlevel after A: %errorlevel%
where cl.exe 2>nul
cl 2>&1 | findstr /C:"Version"
echo === variant B: vcvarsall x64 -vcvars_ver=14.44 ===
call "C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Auxiliary\Build\vcvarsall.bat" x64 -vcvars_ver=14.44.35207
echo errorlevel after B: %errorlevel%
where cl.exe 2>nul
cl 2>&1 | findstr /C:"Version"
