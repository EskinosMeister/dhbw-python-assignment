@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION

:: ------------------------------------
:: Function: choose
:: ------------------------------------
:choose
ECHO How do you want to populate the database?
ECHO 1) Using CSV files
ECHO 2) Using example data
SET /P choice=Enter 1 or 2: 
ECHO %choice%
GOTO :EOF


:: ------------------------------------
:: Function: run_script
:: ------------------------------------
:run_script
IF "%1"=="1"      GOTO run_csv
IF /I "%1"=="csv" GOTO run_csv
IF "%1"=="2"      GOTO run_example
IF /I "%1"=="example" GOTO run_example

ECHO Invalid option.
GOTO :EOF

:run_csv
ECHO Running pop_with_csv.py...
python pop_with_csv.py %*
GOTO :EOF

:run_example
ECHO Running pop_with_example.py...
python pop_with_example.py %*
GOTO :EOF


:: ------------------------------------
:: Main logic
:: ------------------------------------
:: If no arguments provided, ask interactively
IF "%~1"=="" (
    CALL :choose
    CALL :run_script %choice%
) ELSE (
    CALL :run_script %*
)

ENDLOCAL
