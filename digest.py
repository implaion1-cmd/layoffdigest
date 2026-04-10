import anthropic
import smtplib
import os
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def search_and_summarize() -> str:
    """Use Claude with web search to find and summarize life science layoff news."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Today is {date.today()}. Search for news articles published in the last 24 hours "
                    "about layoffs, job cuts, or workforce reductions in the life sciences industry — "
                    "including biotech, pharma, medical devices, and diagnostics companies. "
                    "Write a clear 4-6 sentence summary of the most important developments. "
                    "Include: company names, number of jobs affected (if reported), reasons given, "
                    "and any broader industry trends. If there are no major layoffs in the last 24 hours, "
                    "summarize the most recent significant ones from the past week and note the timeframe."
                ),
            }
        ],
    )

    # Extract the text response (web search results are mixed in with text blocks)
    summary = " ".join(
        block.text for block in response.content if block.type == "text"
    ).strip()

    return summary


def send_email(summary: str) -> None:
    """Send the summary via Gmail SMTP."""
    sender = os.environ["EMAIL_SENDER"]       # your Gmail address
    password = os.environ["EMAIL_PASSWORD"]   # Gmail app password (not your login password)
    recipient = os.environ["EMAIL_RECIPIENT"] # who receives the digest (can be yourself)

    subject = f"Life Science Layoff Digest — {date.today().strftime('%B %d, %Y')}"

    # Build a clean HTML email
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px;">
        <h2 style="color: #2c3e50;">🔬 Life Science Layoff Digest</h2>
        <p style="color: #7f8c8d; font-size: 13px;">{date.today().strftime('%A, %B %d, %Y')}</p>
        <hr style="border: none; border-top: 1px solid #ecf0f1;" />
        <p style="font-size: 15px; line-height: 1.7; color: #2c3e50;">{summary}</p>
        <hr style="border: none; border-top: 1px solid #ecf0f1;" />
        <p style="font-size: 11px; color: #bdc3c7;">Generated automatically by your layoff digest agent.</p>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    print(f"✅ Email sent to {recipient}")


if __name__ == "__main__":
    print("🔍 Searching for life science layoff news...")
    summary = search_and_summarize()
    print(f"\n📝 Summary:\n{summary}\n")

    print("📧 Sending email...")
    send_email(summary)
