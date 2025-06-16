from django.core.mail import send_mail

def send_otp_email(email, otp):
    subject = "Mã OTP xác thực tài khoản"
    message = f"Mã OTP của bạn là: {otp}"
    from_email = None  
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
    return {"status": "success", "message": "OTP sent to email"}