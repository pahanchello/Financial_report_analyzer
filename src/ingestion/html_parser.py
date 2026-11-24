import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup


ITEM_TITLES = {
    "1": "Business",
    "1A": "Risk Factors",
    "1B": "Unresolved Staff Comments",
    "1C": "Cybersecurity",
    "2": "Properties",
    "3": "Legal Proceedings",
    "4": "Mine Safety Disclosures",
    "5": "Market for Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities",
    "6": "Selected Financial Data",
    "7": "Management’s Discussion and Analysis of Financial Condition and Results of Operations",
    "7A": "Quantitative and Qualitative Disclosures About Market Risk",
    "8": "Financial Statements and Supplementary Data",
    "9A": "Controls and Procedures",
    "9B": "Other Information",
    "9C": "Disclosure Regarding Foreign Jurisdictions that Prevent Inspections",
    "10": "Directors, Executive Officers and Corporate Governance",
    "11": "Executive Compensation",
    "12": "Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters",
    "13": "Certain Relationships and Related Transactions, and Director Independence",
    "14": "Principal Accountant Fees and Services",
    "15": "Exhibit and Financial Statement Schedules",
    "16": "Form 10-K Summary",
}

ITEM_ORDER = [
    "1", "1A", "1B", "1C",
    "2", "3", "4",
    "5", "6",
    "7", "7A", "8",
    "9A", "9B", "9C",
    "10", "11", "12", "13", "14", "15", "16",
]

KEEP_ITEMS = {
    "1",
    "1A",
    "1C",
    "2",
    "3",
    "5",
    "7",
    "7A",
    "8",
    "9A",
    "9B",
    "10",
}


class FinancialHTMLParser:
    def __init__(self, min_section_chars: int = 120):
        self.min_section_chars = min_section_chars

        self.item_pattern = re.compile(
            r"(?im)^\s*ITEM\s+([0-9]{1,2}[A-Z]?)\s*\.\s*([^\n\r]*)"
        )

        self.last_report: dict = {}

    def clean_html(self, soup: BeautifulSoup) -> BeautifulSoup:
        for element in soup(
            [
                "script",
                "style",
                "nav",
                "footer",
                "header",
                "noscript",
                "meta",
                "link",
            ]
        ):
            element.decompose()

        return soup

    def clean_text(self, text: str) -> str:
        text = text.replace("\xa0", " ")
        text = text.replace("\ufeff", "")
        text = "".join(
            char
            for char in text
            if unicodedata.category(char)[0] != "C" or char in "\n\r\t"
        )

        text = re.sub(r"[ \t]+", " ", text)

        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(lines)

        text = re.sub(r"\n\s*\n+", "\n\n", text)

        return text.strip()

    def looks_like_toc(self, text: str) -> bool:
        preview = text[:3000]
        lines = [line.strip() for line in preview.splitlines() if line.strip()]

        if not lines:
            return True

        short_text = len(text) < 5000
        numeric_lines = sum(bool(re.fullmatch(r"\d{1,3}", line)) for line in lines)
        item_lines = sum(bool(re.match(r"^Item\b", line, re.IGNORECASE)) for line in lines)

        if short_text and (numeric_lines >= 3 or item_lines >= 3):
            return True

        return False

    def remove_duplicate_heading(self, item_id: str, content: str) -> str:
        content = content.strip()

        content = re.sub(
            rf"^ITEM\s+{re.escape(item_id)}\s*\.\s*[^\n]*\n+",
            "",
            content,
            flags=re.IGNORECASE,
        ).strip()

        title = ITEM_TITLES.get(item_id)
        if title:
            first_line = content.split("\n", 1)[0].strip()
            if first_line.lower() == title.lower():
                content = content.split("\n", 1)[1].strip() if "\n" in content else ""

        return content.strip()

    def extract_metadata(self, html_path: Path, soup: BeautifulSoup) -> dict:
        title = soup.title.get_text(strip=True) if soup.title else "Unknown Title"

        ticker = html_path.stem.split("_")[0].upper()

        fiscal_year: Optional[int] = None
        period_end: Optional[str] = None

        match = re.search(r"(\d{4})(\d{2})(\d{2})", title)
        if match:
            fiscal_year = int(match.group(1))
            period_end = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

        return {
            "filename": html_path.name,
            "title": title,
            "ticker": ticker,
            "fiscal_year": fiscal_year,
            "period_end": period_end,
            "form_type": "10-K",
        }

    def parse_html(self, html_path: str) -> dict:
        html_path = Path(html_path)

        with html_path.open("r", encoding="utf-8") as f:
            content = f.read()

        soup = BeautifulSoup(content, "lxml")
        soup = self.clean_html(soup)

        metadata = self.extract_metadata(html_path, soup)

        text = soup.get_text(separator="\n", strip=True)
        text = self.clean_text(text)

        matches = list(self.item_pattern.finditer(text))

        candidates_by_item: dict[str, list[dict]] = defaultdict(list)

        for idx, match in enumerate(matches):
            item_id = match.group(1).upper()
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)

            raw_section = text[start:end].strip()

            section_content = text[match.end():end].strip()
            section_content = self.remove_duplicate_heading(item_id, section_content)

            candidate = {
                "item_id": item_id,
                "raw_heading": match.group(0).strip(),
                "start_char": start,
                "end_char": end,
                "char_count": len(section_content),
                "looks_like_toc": self.looks_like_toc(section_content),
                "content": section_content,
            }

            candidates_by_item[item_id].append(candidate)

        selected_sections = []
        report_candidates = []

        for item_id in ITEM_ORDER:
            candidates = candidates_by_item.get(item_id, [])

            if not candidates:
                continue

            def score(candidate: dict) -> int:
                value = candidate["char_count"]

                if candidate["looks_like_toc"]:
                    value -= 500_000

                if item_id not in KEEP_ITEMS:
                    value -= 1_000_000

                if candidate["char_count"] < self.min_section_chars:
                    value -= 100_000

                return value

            best = max(candidates, key=score)

            for candidate in candidates:
                report_candidates.append(
                    {
                        "item_id": item_id,
                        "raw_heading": candidate["raw_heading"],
                        "start_char": candidate["start_char"],
                        "end_char": candidate["end_char"],
                        "char_count": candidate["char_count"],
                        "looks_like_toc": candidate["looks_like_toc"],
                        "selected": candidate is best,
                        "kept_in_corpus": (
                            candidate is best
                            and item_id in KEEP_ITEMS
                            and candidate["char_count"] >= self.min_section_chars
                            and not candidate["looks_like_toc"]
                        ),
                        "score": score(candidate),
                    }
                )

            if item_id not in KEEP_ITEMS:
                continue

            if best["char_count"] < self.min_section_chars:
                continue

            if best["looks_like_toc"] and item_id != "8":
                continue

            title = ITEM_TITLES.get(item_id, best["raw_heading"])

            selected_sections.append(
                {
                    "item_id": item_id,
                    "section_title": f"Item {item_id}. {title}",
                    "content": best["content"],
                    "char_count": len(best["content"]),
                    "metadata": {
                        **metadata,
                        "item_id": item_id,
                        "section_title": f"Item {item_id}. {title}",
                        "source_start_char": best["start_char"],
                        "source_end_char": best["end_char"],
                    },
                }
            )

        total_chars = sum(section["char_count"] for section in selected_sections)

        self.last_report = {
            "filename": html_path.name,
            "total_candidates": len(report_candidates),
            "selected_items": [section["item_id"] for section in selected_sections],
            "total_chars": total_chars,
            "candidates": report_candidates,
        }

        return {
            "metadata": {
                **metadata,
                "total_sections": len(selected_sections),
                "total_chars": total_chars,
            },
            "sections": selected_sections,
        }

    def save_parsed_data(self, parsed_data: dict, output_path: str):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)

        print(f"Saved parsed data to {output_path}")

    def save_report(self, report: dict, output_path: str):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"Saved parser report to {output_path}")


def main():
    raw_dir = Path("data/raw/10k")
    html_files = sorted(raw_dir.glob("*.html"))

    if not html_files:
        print("No HTML files found in data/raw/10k")
        return

    parser = FinancialHTMLParser()

    for html_path in html_files:
        print(f"\nParsing {html_path}...")

        parsed_data = parser.parse_html(str(html_path))

        print("\nDocument statistics")
        print("---------------------")
        print(f"Filename: {parsed_data['metadata']['filename']}")
        print(f"Ticker: {parsed_data['metadata']['ticker']}")
        print(f"Fiscal year: {parsed_data['metadata']['fiscal_year']}")
        print(f"Total sections: {parsed_data['metadata']['total_sections']}")
        print(f"Total chars: {parsed_data['metadata']['total_chars']:,}")

        print("\nSections")
        print("--------")
        for section in parsed_data["sections"]:
            print(
                f"{section['item_id']:>3} | "
                f"{section['char_count']:>7,} chars | "
                f"{section['section_title']}"
            )

        output_path = Path("data/processed") / f"{html_path.stem}_parsed.json"
        report_path = Path("data/processed/reports") / f"{html_path.stem}_parser_report.json"

        parser.save_parsed_data(parsed_data, str(output_path))
        parser.save_report(parser.last_report, str(report_path))


if __name__ == "__main__":
    main()