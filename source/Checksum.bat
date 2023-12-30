@echo off
setlocal EnableDelayedExpansion
(set \n=^
%=Don't remove this line=%
)

echo !\n!MD5 Checksums
echo ----------------------------------------------------
echo Windows (exe):!\n!`
certutil -hashfile .\dist\auto-mcs.exe MD5 | find /v "hash"
echo `!\n!Linux (binary):!\n!`
certutil -hashfile .\dist\auto-mcs MD5 | find /v "hash"
echo `!\n!----------------------------------------------------!\n!!\n!
pause
