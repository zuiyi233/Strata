@echo off
rem Incremental stage build: no cache wipe (branch switches rebuild only changed files), tests off
call "C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Auxiliary\Build\vcvarsall.bat" x64 -vcvars_ver=14.44.35207 >nul
if errorlevel 1 exit /b 1
set "PATH=C:\Program Files (x86)\Windows Kits\10\bin\10.0.28000.0\x64;%PATH%"
set "PATH=%PATH:C:\msys64\mingw64\bin;=%"
set "PATH=%PATH:C:\msys64\usr\bin;=%"
where cl.exe >nul 2>&1 || exit /b 1
"N:\Strata\.venv\Scripts\cmake.exe" -S "N:\Strata" -B "N:\Strata\build" -DCMAKE_BUILD_TYPE=Release -DSTRATA_ENABLE_CUDA=ON -DSTRATA_BUILD_TESTS=OFF "-DCMAKE_CUDA_ARCHITECTURES=86-real;75-real" "-DCMAKE_CUDA_COMPILER=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvcc.exe" "-DSTRATA_GGML_DIR=N:\Strata\third_party\llama.cpp" || exit /b 1
"N:\Strata\.venv\Scripts\cmake.exe" --build "N:\Strata\build" --target strata -j 16 && exit /b 0
echo   (the build stopped - trying it once more)
"N:\Strata\.venv\Scripts\cmake.exe" --build "N:\Strata\build" --target strata -j 16 || exit /b 1
