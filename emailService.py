"""This service is for email"""
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import yaml
import logger

# 敏感資訊（帳號密碼）一律由環境變數提供，不寫在 gmail_config.yaml 裡
# 環境變數 -> email_config 欄位
ENV_OVERRIDES = {
    'GMAIL_SENDER_EMAIL': 'sender_email',
    'GMAIL_APP_PASSWORD': 'sender_password',
}

DOTENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')


def load_dotenv(path: str = DOTENV_PATH) -> None:
    """Load KEY=VALUE lines from a .env file into os.environ (existing env vars win)."""
    if not os.path.isfile(path):
        return
    with open(path, 'r', encoding='utf8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            if key.startswith('export '):
                key = key[len('export '):].strip()
            value = value.strip().strip('\'"')
            os.environ.setdefault(key, value)


def load_email_config(config_file: str) -> dict:
    """Read non-sensitive settings from YAML, then fill credentials from env vars."""
    with open(config_file, 'r', encoding='utf8') as f:
        email_config = yaml.safe_load(f)['email']

    load_dotenv()
    for env_key, cfg_key in ENV_OVERRIDES.items():
        if os.environ.get(env_key):
            email_config[cfg_key] = os.environ[env_key]

    missing = [env_key for env_key, cfg_key in ENV_OVERRIDES.items() if not email_config.get(cfg_key)]
    if missing:
        raise KeyError(f"Missing email credentials, please set: {', '.join(missing)} (env var or .env)")
    return email_config


def send_mail(log=None, config_file: str = 'gmail_config.yaml', attaches=None) -> bool:
    """Send email with optional attachments.
    
    Args:
        log: Logger instance (creates one if None)
        config_file: Path to Gmail config YAML file
        attaches: List of file paths to attach
        
    Returns:
        bool: True if email sent successfully
    """
    if attaches is None:
        attaches = []
        
    if log is None:
        log = logger.get_log('log_config.yaml')

    # 讀取YAML檔案 + 環境變數中的帳密
    try:
        email_config = load_email_config(config_file)
    except (FileNotFoundError, KeyError) as e:
        log.exception(e)
        return False

    # 創建MIME多部件消息對象
    msg = MIMEMultipart()
    msg['From'] = email_config['sender_email']
    msg['To'] = ', '.join(email_config['receiver_emails'])
    msg['Subject'] = email_config['subject']

    # 電子郵件正文
    msg.attach(MIMEText(email_config['body'], 'plain'))

    # 附件文件的路徑
    if attaches:
        for attach in attaches:
            # 打開檔案以附件形式加入郵件
            with open(attach, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
                # 編碼附件
                encoders.encode_base64(part)
                
                # 添加附件頭
                separator = str(os.sep)
                file = attach.split(separator).pop()
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {file}',  # 從檔案路徑中提取檔案 
                    )
                
                # 將附件加入到郵件中
                msg.attach(part)


    # 設定SMTP服務器並發送Email
    try:
        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        server.starttls()  # 啟動TLS
        server.login(email_config['sender_email'], email_config['sender_password'])  # 登錄到SMTP服務器
        text = msg.as_string()
        server.sendmail(email_config['sender_email'], email_config['receiver_emails'], text)
        server.quit()
        log.info("Email has sent to %s successfully", email_config['receiver_emails'])
        return True
    except IOError as e:
        log.exception("Failed to send email. Error: %s", e)
        return False


if __name__ == '__main__':
    s = [f'{os.path.curdir}{os.sep}reports{os.sep}kd20_TW_2024-03-04.xlsx']
    send_mail(log=None,attaches=s)
    