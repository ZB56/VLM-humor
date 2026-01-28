"""
Email Parser for .mbox and .eml files

Parses email exports to extract content for humor corpus building.
Optimized for fantasy sports league emails and group threads.
"""

import email
import mailbox
import re
from dataclasses import dataclass
from datetime import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterator
import quopri


@dataclass
class ParsedEmail:
    """Represents a single parsed email."""
    subject: str
    sender: str
    recipients: list[str]
    date: datetime | None
    body: str
    thread_id: str | None = None
    in_reply_to: str | None = None
    message_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "sender": self.sender,
            "recipients": self.recipients,
            "date": self.date.isoformat() if self.date else None,
            "body": self.body,
            "thread_id": self.thread_id,
            "in_reply_to": self.in_reply_to,
            "message_id": self.message_id,
        }


class EmailParser:
    """
    Parse email files (.mbox, .eml) for text extraction.

    Usage:
        parser = EmailParser()

        # Single .eml file
        email = parser.parse_eml("message.eml")

        # Mbox archive
        for email in parser.parse_mbox("archive.mbox"):
            print(email.subject, email.body[:100])
    """

    def __init__(
        self,
        min_body_length: int = 20,
        strip_quotes: bool = True,
        strip_signatures: bool = True,
    ):
        """
        Args:
            min_body_length: Skip emails with body shorter than this
            strip_quotes: Remove quoted reply text (lines starting with >)
            strip_signatures: Remove email signatures
        """
        self.min_body_length = min_body_length
        self.strip_quotes = strip_quotes
        self.strip_signatures = strip_signatures

    def _decode_header_value(self, value: str | None) -> str:
        """Decode encoded email header values."""
        if not value:
            return ""

        decoded_parts = []
        for part, charset in decode_header(value):
            if isinstance(part, bytes):
                charset = charset or 'utf-8'
                try:
                    decoded_parts.append(part.decode(charset, errors='replace'))
                except (LookupError, UnicodeDecodeError):
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(part)

        return ' '.join(decoded_parts)

    def _extract_body(self, msg: email.message.Message) -> str:
        """Extract plain text body from email message."""
        body_parts = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            body_parts.append(payload.decode(charset, errors='replace'))
                        except (LookupError, UnicodeDecodeError):
                            body_parts.append(payload.decode('utf-8', errors='replace'))
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                try:
                    body_parts.append(payload.decode(charset, errors='replace'))
                except (LookupError, UnicodeDecodeError):
                    body_parts.append(payload.decode('utf-8', errors='replace'))

        body = '\n'.join(body_parts)
        return self._clean_body(body)

    def _clean_body(self, body: str) -> str:
        """Clean up email body text."""
        lines = body.split('\n')
        cleaned_lines = []

        for line in lines:
            # Strip quoted text
            if self.strip_quotes and line.strip().startswith('>'):
                continue

            # Detect signature start
            if self.strip_signatures:
                if line.strip() in ('--', '— ', '---', '____'):
                    break
                if re.match(r'^(Sent from|Get Outlook|Sent via)', line.strip(), re.I):
                    break

            cleaned_lines.append(line)

        text = '\n'.join(cleaned_lines)

        # Normalize whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        return text.strip()

    def _parse_recipients(self, msg: email.message.Message) -> list[str]:
        """Extract all recipients (To, Cc)."""
        recipients = []

        for header in ('To', 'Cc'):
            value = msg.get(header)
            if value:
                # Simple extraction - just get email addresses
                addresses = re.findall(r'[\w\.-]+@[\w\.-]+', value)
                recipients.extend(addresses)

        return list(set(recipients))

    def _parse_message(self, msg: email.message.Message) -> ParsedEmail | None:
        """Parse a single email.message.Message object."""
        subject = self._decode_header_value(msg.get('Subject'))
        sender = self._decode_header_value(msg.get('From'))

        # Extract just email address from sender
        sender_match = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        sender_email = sender_match.group() if sender_match else sender

        recipients = self._parse_recipients(msg)

        # Parse date
        date = None
        date_str = msg.get('Date')
        if date_str:
            try:
                date = parsedate_to_datetime(date_str)
            except (ValueError, TypeError):
                pass

        body = self._extract_body(msg)

        if len(body) < self.min_body_length:
            return None

        return ParsedEmail(
            subject=subject,
            sender=sender_email,
            recipients=recipients,
            date=date,
            body=body,
            message_id=msg.get('Message-ID'),
            in_reply_to=msg.get('In-Reply-To'),
            thread_id=msg.get('Thread-Index') or msg.get('References', '').split()[0] if msg.get('References') else None,
        )

    def parse_eml(self, filepath: str | Path) -> ParsedEmail | None:
        """
        Parse a single .eml file.

        Args:
            filepath: Path to the .eml file

        Returns:
            ParsedEmail object or None if parsing fails
        """
        filepath = Path(filepath)

        with open(filepath, 'rb') as f:
            msg = email.message_from_binary_file(f)

        return self._parse_message(msg)

    def parse_mbox(self, filepath: str | Path) -> Iterator[ParsedEmail]:
        """
        Parse an mbox file and yield emails.

        Args:
            filepath: Path to the .mbox file

        Yields:
            ParsedEmail objects
        """
        filepath = Path(filepath)

        mbox = mailbox.mbox(str(filepath))

        for msg in mbox:
            parsed = self._parse_message(msg)
            if parsed:
                yield parsed

    def parse_directory(self, dirpath: str | Path, pattern: str = "*.eml") -> Iterator[ParsedEmail]:
        """
        Parse all email files in a directory.

        Args:
            dirpath: Path to directory
            pattern: Glob pattern for files (default: *.eml)

        Yields:
            ParsedEmail objects
        """
        dirpath = Path(dirpath)

        for email_file in dirpath.glob(pattern):
            if email_file.suffix.lower() == '.mbox':
                yield from self.parse_mbox(email_file)
            else:
                parsed = self.parse_eml(email_file)
                if parsed:
                    yield parsed


def extract_fantasy_threads(
    emails: Iterator[ParsedEmail],
    league_domains: list[str] | None = None,
    subject_keywords: list[str] | None = None,
) -> Iterator[dict]:
    """
    Filter emails for fantasy league content.

    Args:
        emails: Iterator of ParsedEmail objects
        league_domains: Email domains to include (e.g., ['yahoo.com', 'espn.com'])
        subject_keywords: Keywords to match in subject lines

    Yields:
        Filtered email dictionaries
    """
    keywords_lower = [k.lower() for k in (subject_keywords or [
        'fantasy', 'trade', 'waiver', 'lineup', 'matchup',
        'standings', 'draft', 'keeper', 'roster', 'playoffs'
    ])]

    for email_obj in emails:
        # Domain filter
        if league_domains:
            sender_domain = email_obj.sender.split('@')[-1] if '@' in email_obj.sender else ''
            if sender_domain not in league_domains:
                continue

        # Subject keyword filter (looser matching for league emails)
        subject_lower = email_obj.subject.lower()
        if subject_keywords and not any(k in subject_lower for k in keywords_lower):
            continue

        yield email_obj.to_dict()


def group_by_thread(emails: list[dict]) -> dict[str, list[dict]]:
    """
    Group emails by thread/conversation.

    Args:
        emails: List of email dictionaries

    Returns:
        Dictionary mapping thread_id to list of emails
    """
    threads = {}

    for email_obj in emails:
        # Use subject line as fallback thread ID
        thread_id = email_obj.get('thread_id') or email_obj.get('subject', 'unknown')

        # Normalize subject-based thread IDs (strip Re:, Fwd:, etc.)
        if not email_obj.get('thread_id'):
            thread_id = re.sub(r'^(re|fwd|fw):\s*', '', thread_id, flags=re.I)

        if thread_id not in threads:
            threads[thread_id] = []

        threads[thread_id].append(email_obj)

    # Sort each thread by date
    for thread_id in threads:
        threads[thread_id].sort(
            key=lambda x: x.get('date') or '0000-00-00'
        )

    return threads


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Parse email files (.mbox, .eml)")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("-o", "--output", help="Output JSON file", default="emails.json")
    parser.add_argument("--min-length", type=int, default=20, help="Minimum body length")
    parser.add_argument("--no-strip-quotes", action="store_true", help="Keep quoted text")
    parser.add_argument("--domains", nargs="+", help="Filter by sender domains")
    parser.add_argument("--keywords", nargs="+", help="Filter by subject keywords")
    parser.add_argument("--group-threads", action="store_true", help="Group by conversation thread")

    args = parser.parse_args()

    email_parser = EmailParser(
        min_body_length=args.min_length,
        strip_quotes=not args.no_strip_quotes,
    )

    input_path = Path(args.input)

    if input_path.is_dir():
        emails = email_parser.parse_directory(input_path)
    elif input_path.suffix.lower() == '.mbox':
        emails = email_parser.parse_mbox(input_path)
    else:
        result = email_parser.parse_eml(input_path)
        emails = [result] if result else []

    filtered = list(extract_fantasy_threads(emails, args.domains, args.keywords))

    if args.group_threads:
        output_data = group_by_thread(filtered)
    else:
        output_data = filtered

    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Extracted {len(filtered)} emails to {args.output}")
