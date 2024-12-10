"""This service is for email"""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import yaml
import logger
import os



def send_mail(log: any, config_file:str = 'gmail_config.yaml',attaches: list = []) -> bool:

    if log is None:
        log = logger.get_log('emailService_log_config.yaml')

    # 讀取YAML檔案
    try:
        with open('gmail_config.yaml', 'r', encoding='utf8') as f:
            config = yaml.safe_load(f)
            email_config = config['email']
    except FileNotFoundError as e:
        log.exception(e)

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
        log.info(f"Email has sent to {email_config['receiver_emails']} successfully")
    except IOError as e:
        log.exception(f"Failed to send email. Error: {e}")


if __name__ == '__main__':
    s = [f'{os.path.curdir}{os.sep}reports{os.sep}kd20_TW_2024-03-04.xlsx']
    send_mail(log=None,attaches=s)
    