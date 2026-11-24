
import json
import uuid
from pathlib import Path
from typing import List, Dict

class FinancialChunker:
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end < len(text):
                last_period = max(
                    text.rfind('.', start, end),
                    text.rfind('?', start, end),
                    text.rfind('!', start, end)
                )
                
                if last_period > start + self.chunk_size // 2:
                    end = last_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            if start >= end:
                start = end
        
        return chunks
    
    def generate_chunk_id(self, ticker: str, fiscal_year: int, item_id: str, chunk_index: int) -> str:
        unique_str = f"{ticker}_{fiscal_year}_{item_id}_{chunk_index}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_str))
    
    def chunk_sections(self, parsed_data: Dict) -> List[Dict]:
        chunks = []
        
        for section in parsed_data["sections"]:
            text = section["content"]
            item_id = section["item_id"]
            section_title = section["section_title"]
            
            text_chunks = self.chunk_text(text)
            
            for chunk_index, chunk_text in enumerate(text_chunks):
                chunk_id = self.generate_chunk_id(
                    parsed_data["metadata"]["ticker"],
                    parsed_data["metadata"]["fiscal_year"],
                    item_id,
                    chunk_index
                )
                
                chunk = {
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                    "metadata": {
                        "ticker": parsed_data["metadata"]["ticker"],
                        "fiscal_year": parsed_data["metadata"]["fiscal_year"],
                        "period_end": parsed_data["metadata"]["period_end"],
                        "form_type": parsed_data["metadata"]["form_type"],
                        "item_id": item_id,
                        "section_title": section_title,
                        "chunk_index": chunk_index,
                        "total_chunks_in_section": len(text_chunks),
                        "source_filename": parsed_data["metadata"]["filename"]
                    }
                }
                chunks.append(chunk)
        
        return chunks
    
    def save_chunks(self, chunks: List[Dict], output_path: str):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(chunks)} chunks to {output_path}")


def main():
    processed_dir = Path("data/processed")
    parsed_files = sorted(processed_dir.glob("*_parsed.json"))
    
    if not parsed_files:
        print(" No parsed files found in data/processed")
        return
    
    chunker = FinancialChunker(chunk_size=1500, chunk_overlap=200)
    total_chunks = 0
    
    for parsed_file in parsed_files:
        print(f"\n{'='*60}")
        print(f"Processing {parsed_file.name}...")
        print(f"{'='*60}")
        
        with parsed_file.open("r", encoding="utf-8") as f:
            parsed_data = json.load(f)
        
        chunks = chunker.chunk_sections(parsed_data)
        
        ticker = parsed_data["metadata"]["ticker"]
        fiscal_year = parsed_data["metadata"]["fiscal_year"]
        
        print(f"Ticker: {ticker}")
        print(f"Fiscal year: {fiscal_year}")
        print(f"Total sections: {len(parsed_data['sections'])}")
        print(f"Total chunks: {len(chunks)}")
        
        chunks_by_item = {}
        for chunk in chunks:
            item_id = chunk["metadata"]["item_id"]
            chunks_by_item[item_id] = chunks_by_item.get(item_id, 0) + 1
        
        print(f"\nChunks by section:")
        for item_id in sorted(chunks_by_item.keys()):
            print(f"  Item {item_id}: {chunks_by_item[item_id]} chunks")
        
        output_path = processed_dir / "chunks" / f"{parsed_file.stem}_chunks.json"
        chunker.save_chunks(chunks, str(output_path))
        
        total_chunks += len(chunks)
    
    print(f"\n{'='*60}")
    print(f"Total chunks created: {total_chunks}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()