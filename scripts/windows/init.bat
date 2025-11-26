@ECHO OFF
SET SCRIPT_DIR=%~dp0

pip install -r "%SCRIPT_DIR%..\..\requirements.txt"

python "%SCRIPT_DIR%..\..\database\reset_db.py"
python "%SCRIPT_DIR%..\..\database\db_init.py"