
@echo off
setlocal

cd /d "%~dp0data1" || (
    echo Folder data1 tidak ditemukan.
    pause
    exit /b 1
)

if not exist "server_list.dat" (
    echo server_list.dat tidak ditemukan.
    echo Menjalankan db2dat.py...

    python db2dat.py

    if not exist "server_list.dat" (
        echo.
        echo Gagal: server_list.dat belum tersedia.
        pause
        exit /b 1
    )
)

echo.
echo server_list.dat ditemukan.
echo Menjalankan Psiphon...
echo.

ptc.exe --config config.json --serverList server_list.dat

pause
