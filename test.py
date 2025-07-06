import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

message = Mail(
    from_email='noreply@yourproject.com',
    to_emails='user@example.com',
    subject='Password Reset Link',
    html_content='<p>Click <a href="https://yourapp.com/reset?token=abc">here</a> to reset your password.</p>'
)

try:
    sg = SendGridAPIClient('YOUR_SENDGRID_API_KEY')
    response = sg.send(message)
    print("Email sent!", response.status_code)
except Exception as e:
    print(e)