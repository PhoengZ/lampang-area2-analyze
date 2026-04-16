import requests
import json
import os
import fitz  # PyMuPDF
from pathlib import Path

def extract_text_from_bytes(file_bytes, filename, api_key, model, task_type, max_tokens, temperature, top_p, repetition_penalty):
    url = "https://api.opentyphoon.ai/v1/ocr"

    files = {'file': (filename, file_bytes, 'image/jpeg')}
    data = {
        'model': model,
        'task_type': task_type,
        'max_tokens': str(max_tokens),
        'temperature': str(temperature),
        'top_p': str(top_p),
        'repetition_penalty': str(repetition_penalty)
    }

    headers = {
        'Authorization': f'Bearer {api_key}'
    }

    try:
        response = requests.post(url, files=files, data=data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            extracted_texts = []
            # The API returns a list of results for each page (though we send one)
            for page_result in result.get('results', []):
                if page_result.get('success') and page_result.get('message'):
                    content = page_result['message']['choices'][0]['message']['content']
                    try:
                        # Try to parse as JSON if it's structured output
                        parsed_content = json.loads(content)
                        text = parsed_content.get('natural_text', content)
                    except json.JSONDecodeError:
                        text = content
                    extracted_texts.append(text)
                elif not page_result.get('success'):
                    print(f"Error processing {page_result.get('filename', 'unknown')}: {page_result.get('error', 'Unknown error')}")
            return '\n'.join(extracted_texts)
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Exception during OCR request for {filename}: {e}")
        return None

def process_pdf(pdf_path, api_key, model, task_type, max_tokens, temperature, top_p, repetition_penalty):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Could not open {pdf_path}: {e}")
        return ""

    all_extracted_text = []
    # Extract only pages 3n-1 (2nd, 5th, 8th...) -> indices 1, 4, 7...
    # Using 0-based indexing: 3n-1 for n=1,2,3... is 1, 4, 7...
    target_indices = range(1, len(doc), 3)

    if not list(target_indices):
        print(f"No target pages (3n-1) in {pdf_path} (Total pages: {len(doc)})")
        doc.close()
        return ""

    for page_idx in target_indices:
        print(f"  - Extracting page {page_idx + 1}")
        page = doc.load_page(page_idx)
        
        # Convert to image for compression and OCR. 
        # zoom=2.0 (144 DPI) is usually a good balance.
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Compression loop to stay under 4.5 MB
        # In recent PyMuPDF versions, tobytes("jpg") doesn't take the `quality` parameter.
        # So we just get the standard JPG bytes.
        img_bytes = pix.tobytes("jpg")
        
        # If the generated image exceeds 4.5MB, iteratively reduce the zoom (DPI scale) to shrink file size
        while len(img_bytes) > 4.5 * 1024 * 1024 and zoom > 0.5:
            zoom -= 0.3
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("jpg")

        if len(img_bytes) > 4.5 * 1024 * 1024:
            print(f"    Warning: Page {page_idx+1} still exceeds 4.5MB after compression.")

        # Call OCR for this page
        page_text = extract_text_from_bytes(
            img_bytes, f"{pdf_path.stem}_p{page_idx+1}.jpg", api_key, model,
            task_type, max_tokens, temperature, top_p, repetition_penalty
        )

        if page_text:
            all_extracted_text.append(f"--- Page {page_idx+1} ---\n{page_text}")
        else:
            print(f"    Failed to extract text from page {page_idx+1}")

    doc.close()
    return "\n\n".join(all_extracted_text)

def main():
    # Load API Key from environment or .env
    api_key = os.environ.get('TOKEN_KEY')
    if not api_key:
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('TOKEN_KEY='):
                        api_key = line.split('=')[1].strip()
                        break

    if not api_key:
        print("Error: TOKEN_KEY not found in environment or .env file.")
        return

    model = "typhoon-ocr"
    task_type = "default"
    max_tokens = 16384
    temperature = 0.05
    top_p = 0.3
    repetition_penalty = 1

    source_dir = Path('ลำปาง')
    output_dir = Path('compress-ลำปาง')
    output_dir.mkdir(exist_ok=True)

    # Find all PDFs recursively
    pdf_files = sorted(list(source_dir.glob('**/*.pdf')))
    print(f"Found {len(pdf_files)} PDF files to process.")

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path}")
        extracted_text = process_pdf(
            pdf_path, api_key, model, task_type, max_tokens,
            temperature, top_p, repetition_penalty
        )

        if extracted_text:
            # Name file following the name of file read
            output_filename = pdf_path.stem + ".txt"
            output_path = output_dir / output_filename
            
            # Handle potential filename collisions by adding parent folder name if needed
            if output_path.exists():
                output_filename = f"{pdf_path.parent.name}_{pdf_path.stem}.txt"
                output_path = output_dir / output_filename

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            print(f"  Successfully saved to {output_path}")
        else:
            print(f"  No text extracted for {pdf_path}")

if __name__ == "__main__":
    main()
