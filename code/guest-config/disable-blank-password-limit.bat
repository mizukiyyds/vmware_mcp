@echo off
:: 关闭"空白密码本地账户仅允许控制台登录"策略，使 vmrun guest 操作可用空密码账户
:: 需要以管理员身份运行（本脚本自动请求提权）
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v LimitBlankPasswordUse /t REG_DWORD /d 0 /f
if %errorlevel% equ 0 (
    echo [OK] LimitBlankPasswordUse = 0，立即生效，无需重启
) else (
    echo [FAIL] 注册表写入失败
)
pause
