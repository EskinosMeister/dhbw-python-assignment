@ECHO OFF
SET SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%..\..\database\populate_db.py"