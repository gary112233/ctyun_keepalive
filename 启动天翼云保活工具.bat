@echo off
chcp 65001
title 天翼云保活工具 - 最复杂版本
echo.
echo ================================================
echo           天翼云保活工具 - 最复杂版本
echo ================================================
echo.
echo 检测到本地Edge驱动: msedgedriver.exe
echo 云桌面等待时间: 20秒 (确保完全加载)
echo 新增调度器配置界面: 支持自定义保活间隔
echo 正在启动GUI界面...
echo.
python improved_gui.py
echo.
echo 程序已退出，按任意键关闭窗口...
pause > nul