from __future__ import annotations

import os

import resend


class ResendSender:
    def __init__(self) -> None:
        resend.api_key = os.environ["RESEND_API_KEY"]
        self.from_addr: str = os.environ["NEWSLETTER_FROM"]
        self.to_addrs: list[str] = [
            addr.strip() for addr in os.environ["NEWSLETTER_TO"].split(",") if addr.strip()
        ]

    def send(self, subject: str, html: str, plain_text: str) -> dict:
        params: resend.Emails.SendParams = {
            "from": self.from_addr,
            "to": self.to_addrs,
            "subject": subject,
            "html": html,
            "text": plain_text,
        }
        response = resend.Emails.send(params)
        print(f"[resend] Sent to {self.to_addrs}. ID: {response['id']}")
        return response
