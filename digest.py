import anthropic
import smtplib
import os
import json
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def search_and_summarize() -> list[dict]:
    """Use Claude with web search to find and summarize life science layoff news."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Today is {date.today()}. Search for news articles published in the last 24 hours "
                    "about layoffs, job cuts, or workforce reductions in the life sciences industry — "
                    "including biotech, pharma, medical devices, and diagnostics companies. "
                    "If there are no major layoffs in the last 24 hours, use the most recent ones from the past week. "
                    "\n\n"
                    "Return ONLY a JSON array with no markdown, no backticks, no explanation — just raw JSON. "
                    "Each item in the array should have exactly these fields:\n"
                    "  - title: bold headline for the event (e.g. 'Takeda Cuts 634 Jobs in U.S. Restructuring')\n"
                    "  - summary: 1-2 sentences covering what happened, jobs affected, and reason if known\n"
                    "  - url: the direct link to the source article\n"
                    "\n"
                    "Include 3-6 items. Example format:\n"
                    '[{"title": "Acme Bio Lays Off 200", "summary": "Acme Bio cut 200 jobs...", "url": "https://..."}]'
                ),
            }
        ],
    )

    # Extract text blocks and parse JSON
    raw = " ".join(
        block.text for block in response.content if block.type == "text"
    ).strip()

    # Strip any accidental markdown fences
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: return a single item with the raw text if parsing fails
        items = [{"title": "Layoff Digest", "summary": raw, "url": ""}]

    return items


def build_email_html(items: list[dict]) -> str:
    """Build a formatted HTML email from structured layoff items."""

    cards_html = ""
    for item in items:
        title = item.get("title", "Untitled")
        summary = item.get("summary", "")
        url = item.get("url", "")

        source_link = (
            f'<a href="{url}" style="font-size: 13px; color: #2980b9; text-decoration: none;">Read more →</a>'
            if url else ""
        )

        cards_html += f"""
        <div style="margin-bottom: 24px; padding: 16px 20px; border-left: 4px solid #2980b9; background: #f8f9fa; border-radius: 4px;">
          <p style="margin: 0 0 8px 0; font-size: 15px; font-weight: bold; color: #1a252f;">{title}</p>
          <p style="margin: 0 0 10px 0; font-size: 14px; line-height: 1.6; color: #2c3e50;">{summary}</p>
          {source_link}
        </div>
        """

    today_str = date.today().strftime("%A, %B %d, %Y")

    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; max-width: 620px; margin: auto; padding: 24px; background: #ffffff;">

        <div style="margin-bottom: 20px;">
          <h2 style="margin: 0 0 4px 0; color: #1a252f;">🔬 Life Science Layoff Digest</h2>
          <p style="margin: 0; font-size: 13px; color: #7f8c8d;">{today_str}</p>
        </div>

        <hr style="border: none; border-top: 1px solid #ecf0f1; margin-bottom: 24px;" />

        {cards_html}

        <hr style="border: none; border-top: 1px solid #ecf0f1; margin-top: 24px;" />
        <p style="font-size: 11px; color: #bdc3c7; margin-top: 12px;">Generated automatically by your layoff digest agent.</p>

      </body>
    </html>
    """


def send_email(items: list[dict]) -> None:
    """Send the formatted digest via Gmail SMTP."""
    sender = os.environ["EMAIL_SENDER"]
    password = os.environ["EMAIL_PASSWORD"]
    recipient = os.environ["EMAIL_RECIPIENT"]

    subject = f"Life Science Layoff Digest — {date.today().strftime('%B %d, %Y')}"
    html_body = build_email_html(items)

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
    items = search_and_summarize()
    print(f"\n📝 Found {len(items)} items\n")

    print("📧 Sending email...")
    send_email(items)
