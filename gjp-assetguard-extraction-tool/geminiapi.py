import os
import json
import time
import random
from datetime import datetime
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"

def with_retries(func, max_attempts=3, base_delay=2, *args, **kwargs):
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
            print(f"Retry {attempt}/{max_attempts} after error: {e}. Sleeping {delay:.1f}s")
            time.sleep(delay)

def extract_design_criteria_gemini(text, filename):
    """Extract ONLY design criteria sections from OCR text using Gemini API"""
    prompt = f"""
You are an expert engineering document analyzer. Extract ONLY the DESIGN CRITERIA, DESIGN LOADS, or LOADING SPECIFICATIONS sections from this OCR text.

IMPORTANT: Only extract information that appears under clear headings like:
- "DESIGN CRITERIA"
- "DESIGN LOADS"
- "LOADING LOADS"
- "VERTICAL LOADS"
- "HORIZONTAL LOADS"
- "BERTHING LOADS"
- "MOORING LOADS"
- "WIND LOADS"
- "SEISMIC FORCES"
- Sections with load values (kPa, kN, tonnes, m/s, etc.)

SKIP THESE SECTIONS:
- General notes (unless they contain specific load values)
- Construction notes
- Material specs (unless part of design loads)
- Drawing notes
- Standards (unless directly related to loads)

OUTPUT FORMAT - Use this EXACT format:

ITEM: Design Loads (PAGE X)
- [Parameter]: [Value with units]
- [Parameter]: [Value with units]

ITEM: [Next Section Name] (PAGE Y)
- [Parameter]: [Value with units]

METADATA:
- Drawing Number: [Check bottom right corner title block first]
- Project: [From title block or header]
- Location: [Exact site/berth/location name if shown in title block, header, or notes]
- Date: [Check bottom right corner first, then revision history bottom left]
- Revision: [If found]

Document: {filename}

TEXT:
{text}
"""
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    params = {"key": GEMINI_API_KEY}
    response = with_retries(
        lambda: requests.post(GEMINI_API_URL, headers=headers, params=params, json=data)
    )
    if response.status_code == 200:
        result = response.json()
        try:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return "No design criteria extracted."
    else:
        print(f"Gemini API error: {response.status_code} {response.text}")
        return "No design criteria extracted."

def process_document_directory_gemini(dir_path):
    """Process all JSON files in a directory as a single multi-page document (Gemini version)"""
    try:
        json_files = sorted([f for f in os.listdir(dir_path) if f.endswith('.json')])
        if not json_files:
            return f"No JSON files found in {dir_path}"
        document_name = os.path.basename(dir_path)
        combined_text = []
        page_info = []
        for json_file in json_files:
            json_path = os.path.join(dir_path, json_file)
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'responses' in data and len(data['responses']) > 0:
                    response = data['responses'][0]
                    if 'fullTextAnnotation' in response and 'text' in response['fullTextAnnotation']:
                        page_text = response['fullTextAnnotation']['text']
                        page_number = len(combined_text) + 1
                        page_info.append({
                            'page': page_number,
                            'file': json_file,
                            'text_length': len(page_text)
                        })
                        combined_text.append(f"=== PAGE {page_number} ({json_file}) ===\n{page_text}")
            except Exception as e:
                print(f"Warning: Could not process {json_file}: {str(e)}")
                continue
        if not combined_text:
            return f"No valid text found in {dir_path}"
        full_document_text = "\n\n".join(combined_text)
        print(f"   Analyzing {document_name} with Gemini...")
        design_criteria = extract_design_criteria_gemini(full_document_text, document_name)
        return {
            'document_name': document_name,
            'design_criteria': design_criteria,
            'pages_processed': len(page_info),
            'page_info': page_info,
            'processed_at': datetime.now().isoformat()
        }
    except Exception as e:
        return f"Error processing document directory {dir_path}: {str(e)}"

def generate_html_report_gemini(results, output_folder="design_criteria_output_gemini"):
    os.makedirs(output_folder, exist_ok=True)
    summary_file = os.path.join(output_folder, "summary_report.html")
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Engineering Design Criteria Extraction Report (Gemini)</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { background-color: #f4f4f4; padding: 20px; border-radius: 5px; }
        .document-section { margin: 30px 0; border: 1px solid #ddd; padding: 20px; border-radius: 5px; }
        .criteria-content { background-color: #f9f9f9; padding: 15px; border-left: 4px solid #007acc; margin: 10px 0; }
        .metadata { background-color: #e8f4f8; padding: 10px; border-radius: 3px; font-size: 0.9em; }
        .error { color: #d32f2f; }
        .success { color: #388e3c; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Engineering Design Criteria Extraction Report (Gemini)</h1>
        <p><strong>Generated:</strong> """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        <p><strong>Total Documents Processed:</strong> """ + str(len(results)) + """</p>
    </div>
"""
    for dir_path, result in results.items():
        document_name = os.path.basename(dir_path)
        html_content += f"""
    <div class="document-section">
        <h2>{document_name}</h2>
"""
        if isinstance(result, dict):
            html_content += f"""
        <div class="metadata">
            <strong>Status:</strong> <span class="success">Successfully processed</span><br>
            <strong>Pages:</strong> {result.get('pages_processed', 'Unknown')}<br>
            <strong>Processed:</strong> {result.get('processed_at', 'Unknown')}
        </div>
        <h3>Extracted Design Criteria</h3>
        <div class="criteria-content">
            <pre>{result.get('design_criteria', 'No criteria extracted')}</pre>
        </div>
"""
        else:
            html_content += f"""
        <div class="metadata">
            <strong>Status:</strong> <span class="error">Processing failed</span>
        </div>
        <div class="error">
            <pre>{result}</pre>
        </div>
"""
        html_content += "    </div>"
    html_content += """
</body>
</html>
"""
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    for dir_path, result in results.items():
        if isinstance(result, dict):
            document_name = os.path.basename(dir_path)
            individual_file = os.path.join(output_folder, f"document_{document_name}.html")
            individual_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Design Criteria - {document_name} (Gemini)</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
        .criteria-content {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #007acc; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{document_name} (Gemini)</h1>
        <p><strong>Pages Processed:</strong> {result.get('pages_processed', 'Unknown')}</p>
        <p><strong>Generated:</strong> {result.get('processed_at', 'Unknown')}</p>
    </div>
    <h2>Extracted Design Criteria</h2>
    <div class="criteria-content">
        <pre>{result.get('design_criteria', 'No criteria extracted')}</pre>
    </div>
</body>
</html>
"""
            with open(individual_file, 'w', encoding='utf-8') as f:
                f.write(individual_html)
    print(f"HTML reports saved to {output_folder}/")
    print(f"Summary report: {summary_file}")

def save_results_to_file_gemini(results, output_folder="design_criteria_output_gemini"):
    os.makedirs(output_folder, exist_ok=True)
    generate_html_report_gemini(results, output_folder)
    summary_file = os.path.join(output_folder, "extraction_summary.txt")
    with open(summary_file, "w", encoding='utf-8') as f:
        f.write("Design Criteria Extraction Summary (Gemini)\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total documents processed: {len(results)}\n\n")
        for dir_path, result in results.items():
            document_name = os.path.basename(dir_path)
            f.write(f"\nDocument: {document_name}\n")
            f.write("-" * 30 + "\n")
            if isinstance(result, dict):
                f.write(f"Status: Successfully processed\n")
                f.write(f"Pages: {result.get('pages_processed', 'Unknown')}\n")
                f.write(f"Processed: {result.get('processed_at', 'Unknown')}\n\n")
                f.write("Design Criteria:\n")
                f.write(result.get('design_criteria', 'No criteria extracted'))
            else:
                f.write(f"Status: Failed\n")
                f.write(f"Error: {result}\n")
            f.write("\n" + "=" * 50 + "\n")
    for dir_path, result in results.items():
        if isinstance(result, dict):
            document_name = os.path.basename(dir_path)
            individual_file = os.path.join(output_folder, f"document_{document_name}.txt")
            with open(individual_file, "w", encoding='utf-8') as f:
                f.write(f"Design Criteria Extraction - {document_name} (Gemini)\n")
                f.write("=" * 50 + "\n")
                f.write(f"Pages processed: {result.get('pages_processed', 'Unknown')}\n")
                f.write(f"Processed: {result.get('processed_at', 'Unknown')}\n\n")
                f.write("DESIGN CRITERIA:\n")
                f.write("-" * 20 + "\n")
                f.write(result.get('design_criteria', 'No criteria extracted'))

def main():
    output_directories = []
    for i in range(1, 26):
        output_dir = f"output{i}"
        dir_path = f"./ocr_results/{output_dir}"
        if os.path.exists(dir_path):
            output_directories.append(dir_path)
    if not output_directories:
        print("No output directories found in ocr_results")
        return
    print(f"Found {len(output_directories)} documents to process")
    results = {}
    for i, dir_path in enumerate(output_directories, 1):
        document_name = os.path.basename(dir_path)
        print(f"Processing document {i}/{len(output_directories)}: {document_name}")
        try:
            result = process_document_directory_gemini(dir_path)
            results[dir_path] = result
            print(f"✓ Completed: {document_name}")
        except Exception as e:
            error_msg = f"Error processing document {dir_path}: {str(e)}"
            results[dir_path] = error_msg
            print(f"✗ Failed: {document_name} - {str(e)}")
    save_results_to_file_gemini(results)
    print("\nProcessing complete!")
    print(f"Processed {len(results)} documents")
    print("Text summaries saved to design_criteria_output_gemini/")
    print("HTML reports saved to design_criteria_output_gemini/")
    print("Open summary_report.html in your browser to view results!")

if __name__ == "__main__":
    main()
