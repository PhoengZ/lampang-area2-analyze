# lampang-area2-analyze

This project performs OCR on election-related documents using the Typhoon OCR API.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd lampang-area2-analyze
   ```

2. **Set up a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The OCR process requires an API key from OpenTyphoon. Set it as an environment variable:

**Windows (Command Prompt):**
```cmd
set TOKEN_KEY=your_api_key_here
```

**Windows (PowerShell):**
```powershell
$env:TOKEN_KEY="your_api_key_here"
```

**Linux/macOS:**
```bash
export TOKEN_KEY="your_api_key_here"
```

## How to Run

1. Ensure the following directory structure exists:
   - `page-ocr/`: Contains `.txt` files specifying which pages to OCR (one page number per line).
   - `ลำปาง/`: Contains the source `.pdf` files.
   - `ocr-result/`: Output directory for OCR text results.
   - `ocr-success-page/`: Tracking directory for successfully processed pages.

2. Open and run the `ocr_page.ipynb` notebook using Jupyter or VS Code.

The script will:
- Read the page numbers from `page-ocr/*.txt`.
- Locate the corresponding PDF in `ลำปาง/`.
- Extract the specified pages as images.
- Resize images if they exceed the 4MB limit.
- Send them to the Typhoon OCR API.
- Save the results in `ocr-result/` and track progress in `ocr-success-page/`.