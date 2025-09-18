@echo off
echo 开始打包天翼云保活工具...

REM 删除之前的打包文件
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.spec del *.spec

echo 执行PyInstaller打包...

pyinstaller --onedir ^
    --windowed ^
    --name="天翼云保活工具" ^
    --icon=NONE ^
    --add-data="accounts_config.json;." ^
    --add-data="my.json;." ^
    --add-data="msedgedriver.exe;." ^
    --add-data="static;static" ^
    --add-data="logs;logs" ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=tkinter.scrolledtext ^
    --hidden-import=tkinter.filedialog ^
    --hidden-import=tkinter.messagebox ^
    --hidden-import=selenium ^
    --hidden-import=selenium.webdriver ^
    --hidden-import=selenium.webdriver.edge ^
    --hidden-import=selenium.webdriver.common ^
    --hidden-import=requests ^
    --hidden-import=muggle_ocr ^
    --hidden-import=PIL ^
    --hidden-import=logging ^
    --hidden-import=json ^
    --hidden-import=threading ^
    --hidden-import=schedule ^
    improved_gui.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo 打包成功！
    echo 可执行文件位于: dist\天翼云保活工具\
    echo.
    echo 正在复制额外文件...

    REM 复制README和说明文件
    copy README.md "dist\天翼云保活工具\" >nul 2>&1
    copy "GUI使用说明.md" "dist\天翼云保活工具\" >nul 2>&1
    copy "多账号保活使用说明.md" "dist\天翼云保活工具\" >nul 2>&1

    REM 创建启动脚本
    echo @echo off > "dist\天翼云保活工具\启动天翼云保活工具.bat"
    echo cd /d "%%~dp0" >> "dist\天翼云保活工具\启动天翼云保活工具.bat"
    echo "天翼云保活工具.exe" >> "dist\天翼云保活工具\启动天翼云保活工具.bat"

    echo 所有文件已准备完成！
    echo 整个 dist\天翼云保活工具\ 文件夹可以直接复制到其他Windows电脑使用
    pause
) else (
    echo 打包失败！请检查错误信息
    pause
)