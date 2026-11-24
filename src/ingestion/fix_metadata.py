import json
import re
from pathlib import Path

def fix_msft_metadata():
    msft_path = Path("data/processed/MSFT_10K_parsed.json")
    
    with msft_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    filename = data["metadata"]["filename"]
    match = re.search(r"(\d{4})(\d{2})(\d{2})", filename)
    
    if match and data["metadata"]["fiscal_year"] is None:
        year = int(match.group(1))
        data["metadata"]["fiscal_year"] = year
        data["metadata"]["period_end"] = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
        for section in data["sections"]:
            section["metadata"]["fiscal_year"] = year
            section["metadata"]["period_end"] = data["metadata"]["period_end"]
        
        with msft_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f" Fixed MSFT metadata: fiscal_year = {year}")
    else:
        print("MSFT metadata already correct or cannot be fixed")

if __name__ == "__main__":
    fix_msft_metadata()