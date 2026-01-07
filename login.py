
import random,string
import datetime
import smtplib
from email.message import EmailMessage
from passlib.context import CryptContext

def generate_complex_password(n):

    characters = string.ascii_letters + string.digits 
    now = datetime.datetime.now()
    dt_str = now.strftime("%Y%m%d%H%M%S")
    
    # Ensure at least one of each type
    sample_list = [
        random.choice(string.digits),
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase)
    ]
    
    sample_list.extend(random.choices(characters, k=n-4))
    passwd_list = sample_list + list(dt_str)
    random.shuffle(passwd_list)
    return "".join(passwd_list)

#function email sending
def send_mfa_email(to_email: str, code: str):
    msg = EmailMessage()
    msg.set_content(f"Your Secure Login Code is: \n {code}")
    msg["Subject"] = "Your MFA Code"
    msg["From"] = "filecryptwoc@gmail.com"
    msg["To"] = to_email

    html_content = f"""
    <!DOCTYPE html>
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #333333; text-align: center;">Secure Login</h2>
                <p style="font-size: 16px; color: #555555; text-align: center;">
                    Please use the following code to complete your login:
                </p>
                
                <div style="background-color: #e8f0fe; border: 1px solid #d2e3fc; border-radius: 6px; padding: 15px; margin: 20px 0; text-align: center;">
                    <span style="font-family: 'Courier New', monospace; font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #1a73e8;">
                        {code}
                    </span>
                </div>
                
                <p style="font-size: 14px; color: #888888; text-align: center;">
                    If you didn't request this code, you can ignore this email.
                </p>
            </div>
        </body>
    </html>
    """


    msg.set_content(html_content, subtype='html')

    # Connect to Gmail's SMTP server
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("filecryptwoc@gmail.com", "modo mvlx vxpc ifso") #app password for email service from backend
        smtp.send_message(msg)

def login(token_session: bool):
    length = random.randint(12, 15)
    mfa_code = generate_complex_password(length) 

    if(token_session==False):
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
        return mfa_code,expiry_time
    return mfa_code
    

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


