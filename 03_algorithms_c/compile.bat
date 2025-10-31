@echo off
REM Compila a DLL especificamente para 64-bit (para Python 64-bit)

echo Tentando compilar para 64-bit...

REM Adiciona a flag -m64 para forçar a arquitetura
gcc -m64 -shared algorithms.c -o algorithms.dll

echo Comando GCC 64-bit executado.
echo Verifique se houve erros acima e se algorithms.dll foi criado.
pause