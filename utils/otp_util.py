import random
import string
from flask_mail import Message
from extensions import mail

def generate_otp(length=6):
    """Generates a numeric OTP of given length."""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(to_email, otp):
    """Sends the OTP to the specified email address."""
    try:
        msg = Message(
            subject="Your Verification Code - LifeCare Pathology",
            recipients=[to_email],
            body=f"Your verification code is: {otp}\n\nThis code is valid for 10 minutes.\nDo not share this code with anyone.",
            html=f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px; max-width: 500px;">
                <h2 style="color: #FFC107;">LifeCare Pathology Lab</h2>
                <p>Hello,</p>
                <p>Please use the verification code below to complete your registration:</p>
                <div style="background: #f8f9fa; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; border-radius: 5px; margin: 20px 0;">
                    {otp}
                </div>
                <p>This code is valid for 10 minutes.</p>
                <p>If you did not request this, please ignore this email.</p>
            </div>
            """
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending OTP to {to_email}: {e}")
        return False
