@echo off

:: 1. 檢查是否有 "docker" 資料夾，如有則刪除
if exist "docker\" (
    echo [INFO] Found folder "docker", deleting...
    rmdir /s /q "docker"
    echo [INFO] Folder "docker" has been deleted.
) else (
    echo [INFO] Folder "docker" not found.
)

:: 2. 建立新的 "docker" 資料夾
echo [INFO] Creating folder "docker"...
mkdir "docker"

:: 3. 複製 a.py 與 b.py 至 "docker" 資料夾
echo [INFO] Copying files to "docker" folder...
copy "_stock.csv" "docker\"
copy "crontab" "docker\"
copy "Dockerfile" "docker\"
copy "emailService.py" "docker\"
copy "gmail_config.yaml" "docker\"
copy "kd_tools.py" "docker\"
copy "log_config.yaml" "docker\"
copy "logger.py" "docker\"
copy "potential_stars.py" "docker\"
copy "requirements" "docker\"
copy "run.sh" "docker\"
copy "transfer_data.py" "docker\"
copy "yahooBot.py" "docker\"

echo [INFO] All tasks completed.
pause
exit
