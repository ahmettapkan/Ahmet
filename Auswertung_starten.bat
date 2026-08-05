@echo off
rem ---------------------------------------------------------------------
rem  AWL-Auswertung per Doppelklick starten.
rem  Der Ordner mit den Tagesdateien kann auch auf diese Datei
rem  gezogen werden - dann entfaellt die Eingabe.
rem ---------------------------------------------------------------------
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ==========================================================
echo   Kranken-, Urlaubs- und Feiertagsstunden je Kalenderwoche
echo ==========================================================
echo.

rem Ordner entweder per Drag^&Drop (%~1) oder per Eingabe.
set "ORDNER=%~1"
if not defined ORDNER (
    echo Ordner mit den Tagesdateien der Kalenderwoche angeben,
    echo z. B.  Wochen\KW31
    echo.
    set /p "ORDNER=Ordner: "
)

if not defined ORDNER (
    echo.
    echo Kein Ordner angegeben - Abbruch.
    goto :ende
)

rem py bevorzugen, sonst python.
set "PYTHON=py"
where py >nul 2>&1 || set "PYTHON=python"

echo.
%PYTHON% -m awl_auswertung "%ORDNER%" -k konfiguration.json -z "Auswertungen"

if errorlevel 1 (
    echo.
    echo Die Auswertung wurde NICHT erstellt. Meldung oben beachten,
    echo Hilfe dazu in ANLEITUNG.md unter "Wenn etwas nicht funktioniert".
) else (
    echo.
    echo Fertig. Der Bericht liegt im Ordner "Auswertungen".
)

:ende
echo.
pause
endlocal
