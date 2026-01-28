"""
Evernote (.enex) Parser

Parses Evernote export files and extracts text content for humor corpus building.
ENEX files are XML-based with HTML content inside CDATA sections.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterator
import re


class HTMLTextExtractor(HTMLParser):
    """Extract plain text from HTML content."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._skip_data = False
        self._skip_tags = {'style', 'script', 'head', 'meta'}

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip_data = True
        elif tag in ('p', 'div', 'br', 'li', 'tr'):
            self.text_parts.append('\n')

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._skip_data = False

    def handle_data(self, data):
        if not self._skip_data:
            self.text_parts.append(data)

    def get_text(self) -> str:
        text = ''.join(self.text_parts)
        # Normalize whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()


@dataclass
class EvernoteNote:
    """Represents a single Evernote note."""
    title: str
    content: str
    created: datetime | None
    updated: datetime | None
    tags: list[str]
    source_url: str | None = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "content": self.content,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
            "tags": self.tags,
            "source_url": self.source_url,
        }


class EvernoteParser:
    """
    Parse Evernote .enex export files.

    Usage:
        parser = EvernoteParser()
        for note in parser.parse_file("my_notes.enex"):
            print(note.title, note.content[:100])
    """

    def __init__(self, min_content_length: int = 50):
        """
        Args:
            min_content_length: Skip notes with content shorter than this
        """
        self.min_content_length = min_content_length

    def _parse_datetime(self, dt_str: str | None) -> datetime | None:
        """Parse Evernote datetime format: 20231215T143022Z"""
        if not dt_str:
            return None
        try:
            return datetime.strptime(dt_str, "%Y%m%dT%H%M%SZ")
        except ValueError:
            return None

    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract plain text from Evernote's HTML content."""
        extractor = HTMLTextExtractor()
        try:
            extractor.feed(html_content)
            return extractor.get_text()
        except Exception:
            # Fallback: strip tags with regex
            text = re.sub(r'<[^>]+>', ' ', html_content)
            return re.sub(r'\s+', ' ', text).strip()

    def _parse_note_element(self, note_elem: ET.Element) -> EvernoteNote | None:
        """Parse a single <note> element."""
        title_elem = note_elem.find('title')
        title = title_elem.text if title_elem is not None else "Untitled"

        content_elem = note_elem.find('content')
        if content_elem is None or not content_elem.text:
            return None

        content = self._extract_text_from_html(content_elem.text)
        if len(content) < self.min_content_length:
            return None

        created_elem = note_elem.find('created')
        updated_elem = note_elem.find('updated')

        tags = [tag.text for tag in note_elem.findall('tag') if tag.text]

        source_url_elem = note_elem.find('source-url')
        source_url = source_url_elem.text if source_url_elem is not None else None

        return EvernoteNote(
            title=title,
            content=content,
            created=self._parse_datetime(created_elem.text if created_elem is not None else None),
            updated=self._parse_datetime(updated_elem.text if updated_elem is not None else None),
            tags=tags,
            source_url=source_url,
        )

    def parse_file(self, filepath: str | Path) -> Iterator[EvernoteNote]:
        """
        Parse an .enex file and yield notes.

        Args:
            filepath: Path to the .enex file

        Yields:
            EvernoteNote objects
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"ENEX file not found: {filepath}")

        # Parse iteratively to handle large files
        context = ET.iterparse(str(filepath), events=('end',))

        for event, elem in context:
            if elem.tag == 'note':
                note = self._parse_note_element(elem)
                if note:
                    yield note
                # Clear element to save memory
                elem.clear()

    def parse_directory(self, dirpath: str | Path) -> Iterator[EvernoteNote]:
        """
        Parse all .enex files in a directory.

        Args:
            dirpath: Path to directory containing .enex files

        Yields:
            EvernoteNote objects from all files
        """
        dirpath = Path(dirpath)
        for enex_file in dirpath.glob("*.enex"):
            yield from self.parse_file(enex_file)


def extract_humor_snippets(
    notes: Iterator[EvernoteNote],
    tags_filter: list[str] | None = None,
    keyword_filter: list[str] | None = None,
) -> Iterator[dict]:
    """
    Filter notes for humor-relevant content.

    Args:
        notes: Iterator of EvernoteNote objects
        tags_filter: Only include notes with these tags (if specified)
        keyword_filter: Only include notes containing these keywords

    Yields:
        Filtered note dictionaries
    """
    keywords_lower = [k.lower() for k in (keyword_filter or [])]
    tags_lower = [t.lower() for t in (tags_filter or [])]

    for note in notes:
        # Tag filter
        if tags_lower:
            note_tags_lower = [t.lower() for t in note.tags]
            if not any(t in note_tags_lower for t in tags_lower):
                continue

        # Keyword filter
        if keywords_lower:
            content_lower = note.content.lower()
            if not any(k in content_lower for k in keywords_lower):
                continue

        yield note.to_dict()


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Parse Evernote .enex files")
    parser.add_argument("input", help="Input .enex file or directory")
    parser.add_argument("-o", "--output", help="Output JSON file", default="notes.json")
    parser.add_argument("--min-length", type=int, default=50, help="Minimum content length")
    parser.add_argument("--tags", nargs="+", help="Filter by tags")
    parser.add_argument("--keywords", nargs="+", help="Filter by keywords")

    args = parser.parse_args()

    enex_parser = EvernoteParser(min_content_length=args.min_length)
    input_path = Path(args.input)

    if input_path.is_dir():
        notes = enex_parser.parse_directory(input_path)
    else:
        notes = enex_parser.parse_file(input_path)

    filtered = extract_humor_snippets(notes, args.tags, args.keywords)

    results = list(filtered)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Extracted {len(results)} notes to {args.output}")
