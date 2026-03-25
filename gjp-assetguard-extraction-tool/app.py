# app.py — Your code, now with image (PNG/JPG/JPEG) support folded in
# Minimal changes: unified PDF/image handling in GPT/Gemini paths, batch validation for mixed types,
# images use direct Vision API (no GCS upload), side-by-side thumbnails preserved.
import sys
sys.stdout.flush()
sys.stderr.flush()

# Force unbuffered output
import os
os.environ['PYTHONUNBUFFERED'] = '1'

import os
import re
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from fpdf import FPDF
import json
import uuid
import base64
import time
from datetime import datetime
from google.cloud import vision_v1
from google.cloud import storage
from openai import OpenAI
from geminiapi import extract_design_criteria_gemini
from gptapi import extract_design_criteria, extract_metadata_from_text, extract_load_diagram_regions, crop_image_sections

from dotenv import load_dotenv
import shutil

import importlib
import gptapi
importlib.reload(gptapi)

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import blue

from concurrent.futures import ThreadPoolExecutor, as_completed
from progressTracker import progress_status, bp as progress_bp

load_dotenv()

GCP_CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
BUCKET_NAME = os.environ.get("GCP_BUCKET_NAME")

if not GCP_CREDENTIALS_PATH:
    raise RuntimeError("Missing GOOGLE_APPLICATION_CREDENTIALS in .env file or environment.")
if not BUCKET_NAME:
    raise RuntimeError("Missing GCP_BUCKET_NAME in .env file or environment.")

# Initialize clients
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_CREDENTIALS_PATH
vision_client = vision_v1.ImageAnnotatorClient()
storage_client = storage.Client()
openai_client = OpenAI()

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Register progress tracking blueprint
app.register_blueprint(progress_bp)


def with_retries(func, max_attempts=3, base_delay=2, *args, **kwargs):
    import random
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
            print(f"Retry {attempt}/{max_attempts} after error: {e}. Sleeping {delay:.1f}s")
            time.sleep(delay)

# ---------- Session meta helpers ----------
def session_dir_for(session_id):
    return os.path.join(app.config['UPLOAD_FOLDER'], f"session_{session_id}")

def meta_path_for(session_id):
    return os.path.join(session_dir_for(session_id), "meta.json")

def load_meta(session_id):
    try:
        p = meta_path_for(session_id)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"load_meta error: {e}")
    return {}

def save_meta(session_id, meta: dict):
    try:
        os.makedirs(session_dir_for(session_id), exist_ok=True)
        meta["updated_at"] = datetime.now().isoformat()
        with open(meta_path_for(session_id), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
    except Exception as e:
        print(f"save_meta error: {e}")

# ---------- Thumbnails for side-by-side viewer ----------
def save_pdf_pages_to_images(pdf_path, session_id, max_pages=None, dpi=180):
    """Render PDF pages to PNGs; return { '1': '/uploads/session_{id}/page_1.png', ... }"""
    try:
        session_dir = session_dir_for(session_id)
        os.makedirs(session_dir, exist_ok=True)
        doc = fitz.open(pdf_path)
        total = len(doc)
        limit = min(total, max_pages) if max_pages else total
        page_urls = {}
        for i in range(limit):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=dpi)
            name = f"page_{i+1}.png"
            out_path = os.path.join(session_dir, name)
            pix.save(out_path)
            page_urls[str(i+1)] = f"/uploads/session_{session_id}/{name}"
        doc.close()
        return page_urls
    except Exception as e:
        print(f"Failed to render pages: {e}")
        return {}

def annotate_design_criteria_with_diagrams(design_criteria_text, load_diagrams):
    """Add visual indicators to design criteria items with associated load diagrams."""
    if not load_diagrams:
        return design_criteria_text
    
    # Group diagrams by page
    diagrams_by_page = {}
    for diagram in load_diagrams:
        page = diagram.get('page', 1)
        if page not in diagrams_by_page:
            diagrams_by_page[page] = []
        diagrams_by_page[page].append(diagram)
    
    # Process line by line
    lines = design_criteria_text.split('\n')
    annotated_lines = []
    
    for line in lines:
        if line.strip().startswith('ITEM:') and '(PAGE' in line.upper():
            import re
            page_match = re.search(r'\(PAGE\s+(\d+)\)', line, re.IGNORECASE)
            if page_match:
                page_num = int(page_match.group(1))
                if page_num in diagrams_by_page:
                    annotation = f" - Refer to diagram/table on page {page_num}"
                    line = line.rstrip() + annotation
        
        annotated_lines.append(line)
    
    return '\n'.join(annotated_lines)


def _infer_capacity_name(parameter_name, metric):
    p = (parameter_name or "").lower()
    if "axle" in p:
        return "max axle load"
    if "uniform" in p or "udl" in p or "distributed" in p:
        return "max uniform distributor load"
    if "displacement" in p or "vessel" in p:
        return "max displacement size"
    if metric == "kPa":
        return "max uniform distributor load"
    return "max point load"


ALLOWED_CAPACITY_NAMES = {
    "max point load",
    "max axle load",
    "max uniform distributor load",
    "max displacement size",
}

ALLOWED_CAPACITY_METRICS = {"kN", "t", "kPa"}


def _extract_metric(value_text):
    v = (value_text or "").lower()
    if "kpa" in v:
        return "kPa"
    if "kn" in v:
        return "kN"
    if "tonne" in v or "ton" in v or re.search(r"\bt\b", v):
        return "t"
    return None


def build_assetguard_create_asset_payload(design_criteria_text, original_filename, metadata=None):
    """
    Convert criteria text to AssetGuard create-asset JSON shape.
    """
    text = design_criteria_text or ""
    metadata = metadata or {}

    project_name = (metadata.get("project") or "").strip()
    location_name = (metadata.get("location") or "").strip()
    fallback_name = os.path.splitext(os.path.basename(original_filename or "Extracted Asset"))[0]
    asset_name = project_name if project_name and project_name.lower() != "not specified" else fallback_name

    # Collect raw capacities, then deduplicate by (name, metric).
    # When duplicates exist, keep the highest maxLoad and merge details.
    seen: dict[tuple[str, str], dict] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("-") or ":" not in line:
            continue

        param_raw, value_raw = line[1:].split(":", 1)
        param = param_raw.strip()
        value = value_raw.strip()
        if not param or not value:
            continue

        metric = _extract_metric(value)
        if metric is None or metric not in ALLOWED_CAPACITY_METRICS:
            continue

        num_match = re.search(r"[-+]?\d*\.?\d+", value.replace(",", ""))
        if not num_match:
            continue
        max_load = float(num_match.group())
        if max_load <= 0:
            continue

        capacity_name = _infer_capacity_name(param, metric)
        if capacity_name not in ALLOWED_CAPACITY_NAMES:
            continue

        key = (capacity_name, metric)
        detail_text = f"{param}: {value}"
        if key in seen:
            existing = seen[key]
            if max_load > existing["maxLoad"]:
                existing["maxLoad"] = max_load
            existing["_details_parts"].append(detail_text)
        else:
            seen[key] = {
                "name": capacity_name,
                "metric": metric,
                "maxLoad": max_load,
                "_details_parts": [detail_text],
            }

    capacities = []
    for entry in seen.values():
        parts = entry.pop("_details_parts")
        entry["details"] = " | ".join(parts)
        capacities.append(entry)

    if not capacities:
        capacities = [{
            "name": "max point load",
            "metric": "kN",
            "maxLoad": 1.0,
            "details": "Auto-generated fallback. Please edit before importing."
        }]

    return {
        "locationName": location_name if location_name and location_name.lower() != "not specified" else "Unknown Location",
        "name": asset_name or "Extracted Asset",
        "loadCapacities": capacities
    }

def save_image_as_page(image_path, session_id):
    """Save a single input image as page_1.png in the session dir and return the URL map."""
    try:
        session_dir = session_dir_for(session_id)
        os.makedirs(session_dir, exist_ok=True)

        # Normalize to PNG (and flatten if has alpha)
        with Image.open(image_path) as img:
            if img.mode in ("RGBA", "LA"):
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = bg
            out_path = os.path.join(session_dir, "page_1.png")
            img.save(out_path, "PNG")

        return {"1": f"/uploads/session_{session_id}/page_1.png"}, out_path
    except Exception as e:
        print(f"save_image_as_page error: {e}")
        return {}, None

# ---------- GPT extraction ----------
def extract_design_criteria_gpt(text, filename):
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
- Or sections containing load values with units like kPa, kN, tonnes, m/s

DO NOT EXTRACT:
- General notes (unless they contain specific load values)
- Construction notes
- Material specifications (unless part of design loads)
- Dimensions (unless they are load-related)
- Standards references (unless directly related to loads)

OUTPUT FORMAT - Use this EXACT format for compatibility:

ITEM: Design Loads (PAGE X)
- [Parameter]: [Value with units]
- [Parameter]: [Value with units]

ITEM: [Next Section Name] (PAGE Y)
- [Parameter]: [Value with units]

METADATA:
- Drawing Number: [Look in title block, usually bottom right corner]
- Project: [Project name from title block or header]
- Date: [First check bottom right corner box, then check revision history bottom left]
- Revision: [If found]

CRITICAL: You MUST use the exact format "ITEM: [name] (PAGE X)" for each section.
Make sure every ITEM line has (PAGE X) at the end.

Document filename: {filename}

TEXT:
{text}
"""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    result = response.choices[0].message.content
    
    # Validate that we have at least one ITEM
    if "ITEM:" not in result:
        print(f"[WARNING] GPT extraction for {filename} contains no ITEM markers")
        # Return a fallback format
        return f"ITEM: Design Criteria (PAGE 1)\n{result}\n\nMETADATA:\n- Drawing Number: Not specified\n- Project: Not specified\n- Date: Not specified\n- Revision: Not specified"
    
    return result

# ---------- PDF/HTML/Text artifact generation ----------
def generate_pdf_with_images(design_criteria, relevant_sections, filename, output_path):
    try:
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30, textColor=blue, alignment=TA_CENTER)
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, spaceAfter=12, textColor=blue)
        criteria_style = ParagraphStyle('CriteriaStyle', parent=styles['Normal'], fontSize=10, fontName='Courier', leftIndent=20, spaceAfter=12)
        caption_style = ParagraphStyle('CaptionStyle', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Oblique', leftIndent=20, spaceAfter=12)
        story = []
        story.append(Paragraph("Engineering Design Criteria Report", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Document:</b> {filename}", styles['Normal']))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"<b>Relevant Image Sections:</b> {len(relevant_sections)}", styles['Normal']))
        story.append(Spacer(1, 20))
        story.append(Paragraph("Extracted Design Criteria", heading_style))
        for block in (design_criteria or "").split("\n\n"):
            esc = block.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
            story.append(Paragraph(esc, criteria_style))
            story.append(Spacer(1, 6))
        story.append(Spacer(1, 20))
        if relevant_sections:
            story.append(Paragraph("Relevant Engineering Drawing Sections", heading_style))
            story.append(Spacer(1, 12))
            for i, s in enumerate(relevant_sections):
                if os.path.exists(s["path"]):
                    try:
                        story.append(Paragraph(f"Section {i+1}: {s['description']}", heading_style))
                        story.append(Spacer(1, 6))
                        img = Image.open(s["path"])
                        iw, ih = img.size
                        max_w, max_h = 6 * inch, 4 * inch
                        scale = min(max_w / iw, max_h / ih, 1.0)
                        story.append(RLImage(s["path"], width=iw * scale, height=ih * scale))
                        story.append(Spacer(1, 6))
                        story.append(Paragraph(f"<b>Relevance:</b> {s['relevance']}", caption_style))
                        story.append(Spacer(1, 20))
                        if i < len(relevant_sections) - 1:
                            story.append(PageBreak())
                    except Exception as e:
                        story.append(Paragraph("[Image load error]", styles['Normal']))
                        story.append(Spacer(1, 10))
        doc.build(story)
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False

def extract_project_title_from_criteria(design_criteria_text, filename):
    try:
        if not design_criteria_text or design_criteria_text == "Design criteria not available":
            return filename.replace('.pdf', '').replace('_', ' ')
        patterns = [
            r'(?:Project|PROJECT):\s*([^\n\r]+)',
            r'(?:Project|PROJECT)\s*-\s*([^\n\r]+)',
            r'METADATA:.*?(?:Project|PROJECT):\s*([^\n\r]+)',
        ]
        for p in patterns:
            m = re.search(p, design_criteria_text, re.IGNORECASE | re.DOTALL)
            if m:
                t = re.sub(r'\s+', ' ', m.group(1).strip())
                if 3 < len(t) < 100:
                    return t
        for line in (design_criteria_text.split('\n'))[:10]:
            s = line.strip()
            if s and not s.startswith('ITEM:') and not s.startswith('-'):
                if 'project' in s.lower() or 'design' in s.lower():
                    if 5 < len(s) < 100:
                        return s
        return filename.replace('.pdf', '').replace('_', ' ')
    except Exception as e:
        print(f"project title error: {e}")
        return filename.replace('.pdf', '').replace('_', ' ')

def encode_image_to_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"encode_image_to_base64 error: {e}")
        return None

def _wrap_for_fpdf(text: str, hard_wrap_len: int = 80) -> str:
    if not text:
        return ""
    out_lines = []
    pattern = re.compile(rf'(\S{{{hard_wrap_len}}})(?=\S)')
    for raw in text.splitlines():
        line = (raw or "").replace("\u00A0", " ")
        out_lines.append(pattern.sub(lambda m: m.group(1) + '\u00AD', line))
    return "\n".join(out_lines)

def _sanitize_for_fpdf(text: str) -> str:
    if text is None:
        return ""
    s = (text.replace("\u2028", "\n").replace("\u2029", "\n").replace("\r", "").replace("\t", "    ").replace("\u00A0", " "))
    s = s.replace("\\", r"\\")
    s = s.encode("latin1", "replace").decode("latin1")
    return s

# ---------- GCP Vision OCR helper (PDF via GCS) ----------
def _gcp_vision_pdf_to_text(gcs_uri_prefix, blob_name):
    gcs_source_uri = f"gs://{BUCKET_NAME}/{blob_name}"
    gcs_output_folder = gcs_uri_prefix
    gcs_destination_uri = f"gs://{BUCKET_NAME}/{gcs_output_folder}/"

    gcs_source = vision_v1.GcsSource(uri=gcs_source_uri)
    input_config = vision_v1.InputConfig(gcs_source=gcs_source, mime_type="application/pdf")
    gcs_destination = vision_v1.GcsDestination(uri=gcs_destination_uri)
    output_config = vision_v1.OutputConfig(gcs_destination=gcs_destination, batch_size=1)

    async_request = vision_v1.AsyncAnnotateFileRequest(
        features=[vision_v1.Feature(type_=vision_v1.Feature.Type.DOCUMENT_TEXT_DETECTION)],
        input_config=input_config,
        output_config=output_config
    )
    operation = vision_client.async_batch_annotate_files(requests=[async_request])
    print("Waiting for OCR to complete...")
    operation.result(timeout=300)

    blobs = storage_client.list_blobs(BUCKET_NAME, prefix=gcs_output_folder)
    combined_text, page_count = [], 0
    for result_blob in blobs:
        if result_blob.name.endswith(".json"):
            data = json.loads(result_blob.download_as_text())
            if 'responses' in data and data['responses']:
                fta = data['responses'][0].get('fullTextAnnotation', {})
                page_text = fta.get('text', '')
                if page_text.strip():
                    page_count += 1
                    combined_text.append(f"=== PAGE {page_count} ===\n{page_text}")

    return "\n\n".join(combined_text), page_count, gcs_output_folder

# ---------- Shared post-processing for initial (side-by-side) result ----------
def _postprocess_initial_artifacts(session_id, filename, design_criteria, page_count, analysis_images, engine_label):
    # Save TXT for “Initial Text” link
    txt_filename = f"design_criteria_{session_id}.txt"
    txt_path = os.path.join(app.config['UPLOAD_FOLDER'], txt_filename)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(design_criteria or "")
    text_download_url = f"/uploads/{txt_filename}"

    # Crop relevant regions from a few first pages
    all_relevant_sections = []
    for img_path in analysis_images[:3]:
        if os.path.exists(img_path):
            diagrams = extract_load_diagram_regions(img_path, design_criteria)
            if diagrams:
                all_relevant_sections += crop_image_sections(img_path, diagrams, session_dir_for(session_id))

    # PDF
    pdf_filename = f"design_criteria_report_{session_id}.pdf"
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
    pdf_ok = generate_pdf_with_load_images(design_criteria, all_relevant_sections, filename, pdf_path, metadata=None)

    # HTML
    html_filename = f"design_criteria_report_{session_id}.html"
    html_path = os.path.join(app.config['UPLOAD_FOLDER'], html_filename)
    html = f"""<!DOCTYPE html>
<html>
<head>
  <title>Design Criteria Report - {filename}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
    .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
    .criteria {{ background: #f9f9f9; padding: 15px; border-left: 4px solid #007acc; white-space: pre-wrap; }}
    .image-section {{ margin: 20px 0; }}
    .image-item {{ margin: 15px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
    .section-image {{ max-width: 100%; height: auto; border: 1px solid #ccc; }}
    .image-caption {{ font-style: italic; color: #666; font-size: 0.9em; margin-top: 5px; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>Engineering Design Criteria Report</h1>
    <p><strong>Document:</strong> {filename}</p>
    <p><strong>Pages Processed:</strong> {page_count}</p>
    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>Relevant Image Sections:</strong> {len(all_relevant_sections)}</p>
  </div>
  <h2>Extracted Design Criteria</h2>
  <div class="criteria"><pre>{design_criteria}</pre></div>
"""
    if all_relevant_sections:
        html += "<h2>Relevant Engineering Drawing Sections</h2>\n<div class=\"image-section\">\n"
        for i, s in enumerate(all_relevant_sections):
            if os.path.exists(s["path"]):
                b64 = encode_image_to_base64(s["path"])
                if b64:
                    ext = os.path.splitext(s["path"])[1].lower()[1:]
                    html += f"""  <div class="image-item">
    <h4>Section {i+1}: {s['description']}</h4>
    <img src="data:image/{ext};base64,{b64}" class="section-image" alt="{s['description']}">
    <p class="image-caption"><strong>Relevance:</strong> {s['relevance']}</p>
  </div>
"""
        html += "</div>\n"
    html += "</body>\n</html>\n"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    meta = {
        "session_id": session_id,
        "status": "initial",
        "engine": engine_label,
        "original_filename": filename,
        "pages_processed": page_count,
        "artifacts": {"pdf": bool(pdf_ok and os.path.exists(pdf_path)), "html": os.path.exists(html_path), "text": True},
        "created_at": datetime.now().isoformat()
    }
    save_meta(session_id, meta)

    return {
        "success": True,
        "engine": engine_label.lower(),
        "filename": filename,
        "pages_processed": page_count,
        "design_criteria": design_criteria,
        "html_report_url": f"/uploads/{html_filename}",
        "pdf_report_url": f"/uploads/{pdf_filename}" if pdf_ok else None,
        "text_download_url": text_download_url,
        "processed_at": datetime.now().isoformat(),
        "session_id": session_id
    }


def generate_pdf_with_load_images(design_criteria, load_diagrams, filename, output_path, metadata=None):
    """Generate PDF with design criteria and load diagrams"""
    
    try:
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=blue
        )
        
        # Metadata style
        meta_style = ParagraphStyle(
            'Metadata',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=blue
        )
        
        criteria_style = ParagraphStyle(
            'CriteriaStyle',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Courier',
            leftIndent=20,
            spaceAfter=12
        )
        
        # Add title
        story.append(Paragraph("DESIGN CRITERIA REPORT", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Document:</b> {filename}", styles['Normal']))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))

        # Add metadata at the top
        metadata = metadata or {}
        story.append(Paragraph(f"<b>Drawing Number:</b> {metadata.get('drawing_number', 'Not specified')}", meta_style))
        story.append(Paragraph(f"<b>Project:</b> {metadata.get('project', 'Not specified')}", meta_style))
        story.append(Paragraph(f"<b>Date:</b> {metadata.get('date', 'Not specified')}", meta_style))
        story.append(Paragraph(f"<b>Revision:</b> {metadata.get('revision', 'Not specified')}", meta_style))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("Extracted Design Criteria", heading_style))

        # Add design criteria text
        for block in (design_criteria or "").split("\n\n"):
            esc = block.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
            story.append(Paragraph(esc, criteria_style))
            story.append(Spacer(1, 6))
        
        # We no longer add cropped diagram images
        # The annotations in the text now guide users to check the original drawings
        
        doc.build(story)
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False

# ---------- Main GPT path (now: PDF via GCS, IMAGES via direct Vision) ----------
def process_document_with_enhanced_gcp_vision(file_path, filename):
    blob = None
    gcs_output_folder = None
    try:
        # Progress: File preparation stage
        progress_status.file_enter_stage(filename, "file_preparation")
        
        session_id = str(uuid.uuid4())
        session_dir = session_dir_for(session_id)
        os.makedirs(session_dir, exist_ok=True)

        file_ext = os.path.splitext(filename.lower())[1]

        # Always save a copy of the original for history
        original_copy = os.path.join(app.config['UPLOAD_FOLDER'], f"original_{session_id}_{filename}")
        try:
            with open(file_path, "rb") as src, open(original_copy, "wb") as dst:
                dst.write(src.read())
        except Exception as e:
            print(f"Could not save original copy: {e}")

        progress_status.file_complete_stage(filename, "file_preparation")
        analysis_images = []
        page_image_urls = {}

        if file_ext in [".jpg", ".jpeg", ".png"]:
            # Images: direct Vision call (no GCS), single page
            # For images, we skip GCS upload but still mark it as complete for progress tracking
            progress_status.file_complete_stage(filename, "uploading_to_gcs")
            
            progress_status.file_enter_stage(filename, "ocr_processing")
            print("[GPT] Processing image via Vision (direct)...")
            with open(file_path, "rb") as image_file:
                content = image_file.read()
            image = vision_v1.Image(content=content)
            response = vision_client.document_text_detection(image=image)
            if response.error.message:
                raise Exception(f'Vision API error: {response.error.message}')
            full_text = response.full_text_annotation.text if response.full_text_annotation else ""
            if not full_text.strip():
                raise Exception("No text extracted from the image")
            page_count = 1
            progress_status.file_complete_stage(filename, "ocr_processing")

            # Save image as page_1 for side-by-side
            page_image_urls, page1_path = save_image_as_page(file_path, session_id)
            if page1_path:
                analysis_images.append(page1_path)

        else:
            # PDFs: GCS → Vision async JSON
            progress_status.file_enter_stage(filename, "uploading_to_gcs")
            print(f"[GPT] Uploading {filename} to GCS...")
            bucket = storage_client.bucket(BUCKET_NAME)
            blob_name = f"uploads/{session_id}_{filename}"
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(file_path)
            progress_status.file_complete_stage(filename, "uploading_to_gcs")

            # Side-by-side thumbnails
            page_image_urls = save_pdf_pages_to_images(file_path, session_id, max_pages=None, dpi=180)

            # Prepare some analysis rasters
            doc = fitz.open(file_path)
            for page_num in range(min(len(doc), 5)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=150)
                img_path = os.path.join(session_dir, f"page_{page_num + 1}_analysis.png")
                pix.save(img_path)
                analysis_images.append(img_path)
            doc.close()

            # OCR to text
            progress_status.file_enter_stage(filename, "ocr_processing")
            full_text, page_count, gcs_output_folder = _gcp_vision_pdf_to_text(
                gcs_uri_prefix=f"api_output_{session_id}", blob_name=blob_name
            )
            if not full_text.strip():
                raise Exception("No text extracted from the document")
            progress_status.file_complete_stage(filename, "ocr_processing")

        # LLM extraction
        progress_status.file_enter_stage(filename, "ai_analysis")
        print("[GPT] Extracting design criteria…")
        design_criteria = extract_design_criteria(full_text, filename)
        metadata = extract_metadata_from_text(design_criteria)
        progress_status.file_complete_stage(filename, "ai_analysis")

        # Build artifacts
        progress_status.file_enter_stage(filename, "building_artifacts")
        
        # Look for load diagrams
        load_diagrams = []
        for img_path in analysis_images[:3]:
            if os.path.exists(img_path):
                print(f"[GPT] Searching for load diagrams in {os.path.basename(img_path)}...")
                diagrams = extract_load_diagram_regions(img_path, design_criteria)
                if diagrams:
                    print(f"[GPT] Found {len(diagrams)} load diagram(s)")
                    # Add page number to each diagram
                    for diagram in diagrams:
                        if 'page' not in diagram:
                            # Extract page number from filename
                            import re
                            match = re.search(r'page_(\d+)', img_path)
                            if match:
                                diagram['page'] = int(match.group(1))
                            else:
                                diagram['page'] = 1
                    load_diagrams.extend(diagrams)
        
        print(f"[GPT] Total load diagrams extracted: {len(load_diagrams)}")
        
        # Annotate design criteria with diagram references
        if load_diagrams:
            print(f"[GPT] Annotating design criteria with diagram references...")
            design_criteria = annotate_design_criteria_with_diagrams(design_criteria, load_diagrams)

        # Save text file
        txt_filename = f"design_criteria_{session_id}.txt"
        txt_path = os.path.join(app.config['UPLOAD_FOLDER'], txt_filename)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(design_criteria or "")

        json_filename = f"design_criteria_asset_payload_{session_id}.json"
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
        payload = build_assetguard_create_asset_payload(design_criteria, filename, metadata)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        # Generate PDF with simple format
        pdf_filename = f"design_criteria_report_{session_id}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        pdf_ok = generate_pdf_with_load_images(design_criteria, load_diagrams, filename, pdf_path, metadata)

        # Generate HTML
        html_filename = f"design_criteria_report_{session_id}.html"
        html_path = os.path.join(app.config['UPLOAD_FOLDER'], html_filename)

        # Extract project title for HTML
        project_title = metadata.get('project', filename.replace('.pdf', '').replace('_', ' '))
        
        
        # Save HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Design Criteria Report - {filename}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .criteria {{ background: #f9f9f9; padding: 15px; border-left: 4px solid #007acc; white-space: pre-wrap; font-family: monospace; }}
        .metadata {{ background: #e8f4f8; padding: 10px; border-radius: 3px; margin-bottom: 20px; }}
        .note {{ background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Engineering Design Criteria Report</h1>
        <p><strong>Document:</strong> {filename}</p>
        <p><strong>Pages Processed:</strong> {page_count}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="metadata">
        <h3>Document Information</h3>
        <p><strong>Drawing Number:</strong> {metadata.get('drawing_number', 'Not specified')}</p>
        <p><strong>Project:</strong> {project_title}</p>
        <p><strong>Date:</strong> {metadata.get('date', 'Not specified')}</p>
        <p><strong>Revision:</strong> {metadata.get('revision', 'Not specified')}</p>
    </div>
    
    <h2>Extracted Design Criteria</h2>
    <div class="criteria">{design_criteria}</div>
"""
        
        if load_diagrams:
            html += """
    <div class="note">
        <strong>Note:</strong> This document contains load diagrams and tables. 
        This indicate that relevant diagrams/tables can be found on the specified page in the original drawing.
    </div>
"""
        
        html += f"""
</body>
</html>
"""
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        progress_status.file_complete_stage(filename, "building_artifacts")
        
        # Update meta
        meta = {
            "session_id": session_id,
            "status": "initial",
            "engine": "GPT",
            "original_filename": filename,
            "pages_processed": page_count,
            "load_diagrams": load_diagrams,
            "artifacts": {
                "pdf": bool(pdf_ok and os.path.exists(pdf_path)),
                "html": os.path.exists(html_path),
                "text": True,
                "json": os.path.exists(json_path)
            },
            "created_at": datetime.now().isoformat()
        }
        save_meta(session_id, meta)
        
        # Mark file as completely finished
        progress_status.file_complete_stage(filename, "completed")
        time.sleep(0.1)  # Give frontend time to update progress
        
        return {
            "success": True,
            "engine": "gpt",
            "filename": filename,
            "pages_processed": page_count,
            "design_criteria": design_criteria,
            "html_report_url": f"/uploads/{html_filename}",
            "pdf_report_url": f"/uploads/{pdf_filename}" if pdf_ok else None,
            "json_download_url": f"/uploads/{json_filename}",
            "text_download_url": f"/uploads/{txt_filename}",
            "processed_at": datetime.now().isoformat(),
            "session_id": session_id,
            "page_image_urls": page_image_urls,
            "original_file_url": f"/uploads/original_{session_id}_{filename}" if os.path.exists(original_copy) else None
        }
        

    except Exception as e:
        print(f"[GPT] Error: {e}")
        return {"success": False, "engine": "gpt", "error": str(e), "filename": filename}
    finally:
        try:
            if blob and blob.exists():
                blob.delete()
        except Exception as ce:
            print(f"[GPT] Blob cleanup failed: {ce}")
        try:
            if gcs_output_folder:
                for b in storage_client.list_blobs(BUCKET_NAME, prefix=gcs_output_folder):
                    b.delete()
        except Exception as ce:
            print(f"[GPT] OCR cleanup failed: {ce}")

# ---------- Gemini path (now: image support + existing PDF flow) ----------
def process_document_with_gcp_vision_gemini(file_path, filename):
    blob = None
    gcs_output_folder = None
    try:
        # Progress: File preparation stage
        progress_status.file_enter_stage(filename, "file_preparation")
        
        session_id = str(uuid.uuid4())
        session_dir = session_dir_for(session_id)
        os.makedirs(session_dir, exist_ok=True)

        file_ext = os.path.splitext(filename.lower())[1]

        # Save original for history
        original_copy = os.path.join(app.config['UPLOAD_FOLDER'], f"original_{session_id}_{filename}")
        try:
            with open(file_path, "rb") as src, open(original_copy, "wb") as dst:
                dst.write(src.read())
        except Exception as e:
            print(f"[Gemini] Could not save original copy: {e}")

        progress_status.file_complete_stage(filename, "file_preparation")
        full_text = ""
        page_count = 0
        page_image_urls = {}
        analysis_images = []

        if file_ext in [".jpg", ".jpeg", ".png"]:
            # For images, we skip GCS upload but still mark it as complete for progress tracking
            progress_status.file_complete_stage(filename, "uploading_to_gcs")
            
            progress_status.file_enter_stage(filename, "ocr_processing")
            print("[Gemini] Processing image via Vision (direct)...")
            with open(file_path, "rb") as image_file:
                content = image_file.read()
            image = vision_v1.Image(content=content)
            response = vision_client.document_text_detection(image=image)
            if response.error.message:
                raise Exception(f'Vision API error: {response.error.message}')
            full_text = response.full_text_annotation.text if response.full_text_annotation else ""
            if not full_text.strip():
                raise Exception("No text extracted from the image")
            page_count = 1
            progress_status.file_complete_stage(filename, "ocr_processing")

            # Side-by-side page
            page_image_urls, page1_path = save_image_as_page(file_path, session_id)
            if page1_path:
                analysis_images.append(page1_path)

        else:
            progress_status.file_enter_stage(filename, "uploading_to_gcs")
            print(f"[Gemini] Uploading {filename} to GCS...")
            bucket = storage_client.bucket(BUCKET_NAME)
            blob_name = f"uploads/{session_id}_{filename}"
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(file_path)
            progress_status.file_complete_stage(filename, "uploading_to_gcs")

            # Thumbnails for split UI
            page_image_urls = save_pdf_pages_to_images(file_path, session_id, max_pages=None, dpi=180)

            # Prepare some analysis rasters (FIXED: Added for Gemini PDF path)
            doc = fitz.open(file_path)
            for page_num in range(min(len(doc), 5)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=150)
                img_path = os.path.join(session_dir, f"page_{page_num + 1}_analysis.png")
                pix.save(img_path)
                analysis_images.append(img_path)
            doc.close()

            # OCR to text
            progress_status.file_enter_stage(filename, "ocr_processing")
            full_text, page_count, gcs_output_folder = _gcp_vision_pdf_to_text(
                gcs_uri_prefix=f"api_output_gemini_{session_id}", blob_name=blob_name
            )
            if not full_text.strip():
                raise Exception("No text extracted (Gemini)")
            progress_status.file_complete_stage(filename, "ocr_processing")

        progress_status.file_enter_stage(filename, "ai_analysis")
        print("[Gemini] Extracting design criteria…")
        
        design_criteria = extract_design_criteria_gemini(full_text, filename)
        metadata = extract_metadata_from_text(design_criteria)
        progress_status.file_complete_stage(filename, "ai_analysis")

        # Build artifacts
        progress_status.file_enter_stage(filename, "building_artifacts")

        # Look for load diagrams (Gemini version)
        load_diagrams = []
        for img_path in analysis_images[:3]:
            if os.path.exists(img_path):
                print(f"[Gemini] Searching for load diagrams in {os.path.basename(img_path)}...")
                diagrams = extract_load_diagram_regions(img_path, design_criteria)
                if diagrams:
                    print(f"[Gemini] Found {len(diagrams)} load diagram(s)")
                    # Add page number to each diagram
                    for diagram in diagrams:
                        if 'page' not in diagram:
                            import re
                            match = re.search(r'page_(\d+)', img_path)
                            if match:
                                diagram['page'] = int(match.group(1))
                            else:
                                diagram['page'] = 1
                    load_diagrams.extend(diagrams)
        
        print(f"[Gemini] Total load diagrams detected: {len(load_diagrams)}")
        
        # Annotate design criteria with diagram references
        if load_diagrams:
            print(f"[Gemini] Annotating design criteria with diagram references...")
            design_criteria = annotate_design_criteria_with_diagrams(design_criteria, load_diagrams)

        # Save text
        txt_filename = f"design_criteria_{session_id}.txt"
        txt_path = os.path.join(app.config['UPLOAD_FOLDER'], txt_filename)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(design_criteria or "")

        json_filename = f"design_criteria_asset_payload_{session_id}.json"
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
        payload = build_assetguard_create_asset_payload(design_criteria, filename, metadata)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        # Generate PDF with simple format
        pdf_filename = f"design_criteria_report_{session_id}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        pdf_ok = generate_pdf_with_load_images(design_criteria, load_diagrams, filename, pdf_path ,metadata)
        
        # Generate HTML
        html_filename = f"design_criteria_report_{session_id}.html"
        html_path = os.path.join(app.config['UPLOAD_FOLDER'], html_filename)

        # Extract project title for HTML
        project_title = metadata.get('project', filename.replace('.pdf', '').replace('_', ' '))
        
        # Generate HTML content
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Design Criteria Report - {filename}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .criteria {{ background: #f9f9f9; padding: 15px; border-left: 4px solid #007acc; white-space: pre-wrap; font-family: monospace; }}
        .metadata {{ background: #e8f4f8; padding: 10px; border-radius: 3px; margin-bottom: 20px; }}
        .note {{ background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Engineering Design Criteria Report</h1>
        <p><strong>Document:</strong> {filename}</p>
        <p><strong>Pages Processed:</strong> {page_count}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="metadata">
        <h3>Document Information</h3>
        <p><strong>Drawing Number:</strong> {metadata.get('drawing_number', 'Not specified')}</p>
        <p><strong>Project:</strong> {project_title}</p>
        <p><strong>Date:</strong> {metadata.get('date', 'Not specified')}</p>
        <p><strong>Revision:</strong> {metadata.get('revision', 'Not specified')}</p>
    </div>
"""
        
        if load_diagrams:
            html_content += """
    <div class="note">
        <strong>Note:</strong> This document contains load diagrams and tables. 
        This indicates that relevant diagrams/tables can be found on the specified page in the original drawing.
    </div>
"""
        
        html_content += f"""
    <h2>Extracted Design Criteria</h2>
    <div class="criteria">{design_criteria}</div>
</body>
</html>"""
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        progress_status.file_complete_stage(filename, "building_artifacts")
        
        # Update meta
        meta = {
            "session_id": session_id,
            "status": "initial",
            "engine": "Gemini",
            "original_filename": filename,
            "pages_processed": page_count,
            "load_diagrams": load_diagrams,
            "artifacts": {
                "pdf": bool(pdf_ok and os.path.exists(pdf_path)),
                "html": os.path.exists(html_path),
                "text": True,
                "json": os.path.exists(json_path)
            },
            "created_at": datetime.now().isoformat()
        }
        save_meta(session_id, meta)

        # Mark file as completely finished
        progress_status.file_complete_stage(filename, "completed")
        time.sleep(0.1)  # Give frontend time to update progress
        
        result = {
            "success": True,
            "engine": "gemini",
            "filename": filename,
            "pages_processed": page_count,
            "design_criteria": design_criteria,
            "html_report_url": f"/uploads/{html_filename}",
            "pdf_report_url": f"/uploads/{pdf_filename}" if pdf_ok else None,
            "json_download_url": f"/uploads/{json_filename}",
            "text_download_url": f"/uploads/{txt_filename}",
            "processed_at": datetime.now().isoformat(),
            "session_id": session_id,
            "page_image_urls": page_image_urls,
            "original_file_url": f"/uploads/original_{session_id}_{filename}" if os.path.exists(original_copy) else None
        }
        
        return result

    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return {"success": False, "engine": "gemini", "error": str(e), "filename": filename}
    finally:
        try:
            if blob and blob.exists():
                blob.delete()
        except Exception as ce:
            print(f"[Gemini] Blob cleanup failed: {ce}")
        try:
            if gcs_output_folder:
                for b in storage_client.list_blobs(BUCKET_NAME, prefix=gcs_output_folder):
                    b.delete()
        except Exception as ce:
            print(f"[Gemini] OCR cleanup failed: {ce}")

# ---------- Batch upload endpoint (now validates/accepts mixed types) ----------
@app.route('/api/process-batch-documents', methods=['POST'])
def process_batch_documents():
    try:
        files = request.files.getlist('files') or request.files.getlist('file')
        model = request.form.get('model', 'gpt')
        if not files:
            return jsonify({'success': False, 'error': 'No files uploaded (use field name "files")'}), 400

        # Initialize progress tracking for batch processing
        valid_files = [f for f in files if f and f.filename]
        progress_status.reset()
        progress_status.start_batch(len(valid_files))
        
        # Mark initialization as complete for all files
        for f in valid_files:
            progress_status.file_complete_stage(f.filename, "initializing")

        ALLOWED_EXT = {'.pdf', '.jpg', '.jpeg', '.png'}
        results = []
        MAX_WORKERS = 4

        def _process_one(fs_file):
            if not fs_file or not fs_file.filename:
                return {'success': False, 'error': 'Empty filename'}
            raw_name = secure_filename(fs_file.filename)
            ext = os.path.splitext(raw_name.lower())[1]
            if ext not in ALLOWED_EXT:
                return {'success': False, 'filename': raw_name, 'error': f'Unsupported file format: {ext}. Supported: PDF, JPG, JPEG, PNG'}

            tmp_name = f"batch_{uuid.uuid4().hex[:8]}_{raw_name}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], tmp_name)
            fs_file.save(save_path)
            try:
                if model == 'gemini':
                    result = process_document_with_gcp_vision_gemini(save_path, raw_name)
                else:
                    result = process_document_with_enhanced_gcp_vision(save_path, raw_name)
            except Exception as e:
                result = {'success': False, 'filename': raw_name, 'error': str(e)}
            finally:
                try:
                    if os.path.exists(save_path):
                        os.remove(save_path)
                except Exception:
                    pass

            # Ensure convenience fields for UI
            if isinstance(result, dict) and result.get('success') and result.get('session_id'):
                sid = result['session_id']
                orig_name = f"original_{sid}_{raw_name}"
                orig_path = os.path.join(app.config['UPLOAD_FOLDER'], orig_name)
                result['original_filename'] = raw_name
                result['original_file_url'] = f"/uploads/{orig_name}" if os.path.exists(orig_path) else None
            if isinstance(result, dict) and 'filename' not in result:
                result['filename'] = raw_name
            return result

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = {ex.submit(_process_one, f): f.filename for f in files if f and f.filename}
            for fut in as_completed(futures):
                results.append(fut.result())

        return jsonify({'success': True, 'results': results, 'count': len(results)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ---------- History ----------
@app.route('/api/previous-results', methods=['GET'])
def get_previous_results():
    try:
        uploads_dir = app.config['UPLOAD_FOLDER']
        results = []
        for name in os.listdir(uploads_dir):
            if not name.startswith("session_"):
                continue
            session_id = name.replace("session_", "")
            sdir = os.path.join(uploads_dir, name)
            meta = load_meta(session_id) or {"session_id": session_id, "status": "initial"}

            pdf_fn  = f"design_criteria_report_{session_id}.pdf"
            html_fn = f"design_criteria_report_{session_id}.html"
            txt_fn  = f"design_criteria_{session_id}.txt"
            final_txt_fn = f"final_design_criteria_{session_id}.txt"
            json_fn = f"design_criteria_asset_payload_{session_id}.json"
            final_json_fn = f"final_design_criteria_asset_payload_{session_id}.json"

            pdf_path  = os.path.join(uploads_dir, pdf_fn)
            html_path = os.path.join(uploads_dir, html_fn)
            txt_path  = os.path.join(uploads_dir, final_txt_fn) if os.path.exists(os.path.join(uploads_dir, final_txt_fn)) else os.path.join(uploads_dir, txt_fn)
            json_path = os.path.join(uploads_dir, final_json_fn) if os.path.exists(os.path.join(uploads_dir, final_json_fn)) else os.path.join(uploads_dir, json_fn)

            pdf_url  = f"/uploads/{pdf_fn}"  if os.path.exists(pdf_path) else None
            html_url = f"/uploads/{html_fn}" if os.path.exists(html_path) else None
            txt_url  = f"/uploads/{os.path.basename(txt_path)}"  if os.path.exists(txt_path) else None
            json_url = f"/uploads/{os.path.basename(json_path)}" if os.path.exists(json_path) else None

            # ALWAYS find original
            original_url, original_name = None, f"Session_{session_id[:8]}"
            orig_prefix = f"original_{session_id}_"
            for fn in os.listdir(uploads_dir):
                if fn.startswith(orig_prefix):
                    original_url  = f"/uploads/{fn}"
                    original_name = fn.split("_", 2)[-1]
                    break

            design_criteria = "Design criteria not available"
            if txt_url:
                try:
                    with open(txt_path, "r", encoding="utf-8") as f:
                        design_criteria = f.read()
                except Exception as e:
                    design_criteria = f"(Could not read criteria: {e})"

            project_title = extract_project_title_from_criteria(design_criteria, original_name)

            session_files = []
            if os.path.isdir(sdir):
                for sf in os.listdir(sdir):
                    sp = os.path.join(sdir, sf)
                    if os.path.isfile(sp):
                        session_files.append({"name": sf, "url": f"/uploads/{name}/{sf}", "size": os.path.getsize(sp)})

            latest = meta.get("final_generated_at") or meta.get("updated_at") or meta.get("created_at") or datetime.now().isoformat()
            earliest = meta.get("created_at") or latest

            results.append({
                "session_id": session_id,
                "original_filename": original_name,
                "project_title": project_title or original_name,
                "original_file_url": original_url,
                "earliest_generated": earliest,
                "latest_generated": latest,
                "reports": [{
                    "report_type": "final" if meta.get("status") == "final" else "initial",
                    "generated_at": latest,
                    "pdf_report_url": pdf_url,
                    "html_report_url": html_url,
                    "json_download_url": json_url,
                    "text_download_url": txt_url,
                    "design_criteria": design_criteria
                }],
                "session_files": session_files,
                "session_directory": f"session_{session_id}",
                "is_merged": False
            })

        results.sort(key=lambda x: x["latest_generated"], reverse=True)
        return jsonify({"success": True, "results": results})
    except Exception as e:
        print(f"Error retrieving previous results: {str(e)}")
        return jsonify({"error": f"Failed to retrieve previous results: {str(e)}"}), 500

# ---------- Delete / Clear ----------
@app.route('/api/delete-report', methods=['POST'])
def delete_report():
    try:
        data = request.get_json()
        if not data or 'session_id' not in data:
            return jsonify({"error": "Session ID is required"}), 400
        session_id = data['session_id']
        uploads_dir = app.config['UPLOAD_FOLDER']
        deleted_files = 0
        for filename in os.listdir(uploads_dir):
            if (filename.startswith(f'design_criteria_report_{session_id}') or 
                filename.startswith(f'design_criteria_asset_payload_{session_id}') or
                filename.startswith(f'final_design_criteria_asset_payload_{session_id}') or
                filename.startswith(f'final_design_criteria_{session_id}') or
                filename.startswith(f'original_{session_id}_') or
                filename == f'session_{session_id}' or
                filename.startswith(f'session_{session_id}_')):
                try:
                    path = os.path.join(uploads_dir, filename)
                    if os.path.exists(path):
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                        deleted_files += 1
                except Exception as e:
                    print(f"Could not delete {filename}: {e}")
        if deleted_files == 0:
            return jsonify({"error": f"No files found for session ID: {session_id}"}), 404
        return jsonify({"success": True, "message": f"Report deleted. Removed {deleted_files} files.", "deleted_files": deleted_files})
    except Exception as e:
        print(f"Error deleting report: {str(e)}")
        return jsonify({"error": f"Failed to delete report: {str(e)}"}), 500

@app.route('/api/clear-previous-results', methods=['POST'])
def clear_previous_results():
    try:
        uploads_dir = app.config['UPLOAD_FOLDER']
        cleared = 0
        for filename in os.listdir(uploads_dir):
            if (filename.startswith('design_criteria_report_') or 
                filename.startswith('design_criteria_asset_payload_') or
                filename.startswith('final_design_criteria_asset_payload_') or
                filename.startswith('final_design_criteria_') or
                filename.startswith('original_') or
                filename.startswith('session_')):
                try:
                    path = os.path.join(uploads_dir, filename)
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    cleared += 1
                except Exception as e:
                    print(f"Could not clear {filename}: {e}")
        return jsonify({"success": True, "message": f"Cleared {cleared} previous result files", "cleared_count": cleared})
    except Exception as e:
        print(f"Error clearing previous results: {str(e)}")
        return jsonify({"error": f"Failed to clear previous results: {str(e)}"}), 500

# ---------- Final report (kept) ----------
@app.route('/api/generate-final-report', methods=['POST'])
def generate_final_report():
    try:
        data = request.get_json()
        if not data or 'design_criteria' not in data:
            return jsonify({"error": "No design criteria provided"}), 400

        edited_criteria = data['design_criteria']
        original_filename = data.get('original_filename', 'document.pdf')
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400

        # Extract metadata from the edited criteria text
        metadata = extract_metadata_from_text(edited_criteria)

        session_dir = session_dir_for(session_id)
        load_diagrams = []

        # Check if we have saved diagram detection results
        meta = load_meta(session_id)
        if meta.get('load_diagrams'):
            load_diagrams = meta['load_diagrams']
            print(f"[Final Report] Restored {len(load_diagrams)} diagram references from metadata")
        
        # Re-annotate the edited criteria with diagram references
        if load_diagrams:
            print(f"[Final Report] Re-annotating edited criteria with diagram references...")
            edited_criteria = annotate_design_criteria_with_diagrams(edited_criteria, load_diagrams)

        all_relevant_sections = []
        # We no longer use cropped sections

        pdf_filename  = f"design_criteria_report_{session_id}.pdf"
        pdf_path      = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        html_filename = f"design_criteria_report_{session_id}.html"
        html_path     = os.path.join(app.config['UPLOAD_FOLDER'], html_filename)
        text_filename = f"final_design_criteria_{session_id}.txt"
        text_path     = os.path.join(app.config['UPLOAD_FOLDER'], text_filename)

        pdf_ok = generate_pdf_with_load_images(edited_criteria, all_relevant_sections, original_filename, pdf_path, metadata)
        
        project_title = metadata.get('project', original_filename.replace('.pdf', '').replace('_', ' '))

        html = f"""<!DOCTYPE html>
<html>
<head>
  <title>Final Design Criteria Report - {original_filename}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
    .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
    .criteria {{ background: #f9f9f9; padding: 15px; border-left: 4px solid #007acc; white-space: pre-wrap; font-family: monospace; }}
    .metadata {{ background: #e8f4f8; padding: 10px; border-radius: 3px; margin-bottom: 20px; }}
    .edit-note {{ background: #d4edda; padding: 10px; border-left: 4px solid #28a745; border-radius: 5px; margin-bottom: 15px; }}
    .note {{ background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0; border-radius: 5px; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>Final Engineering Design Criteria Report</h1>
    <p><strong>Document:</strong> {original_filename}</p>
    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>Status:</strong> User-Edited Content</p>
  </div>

  <div class="metadata">
    <h3>Document Information</h3>
    <p><strong>Drawing Number:</strong> {metadata.get('drawing_number', 'Not specified')}</p>
    <p><strong>Project:</strong> {project_title}</p>
    <p><strong>Date:</strong> {metadata.get('date', 'Not specified')}</p>
    <p><strong>Revision:</strong> {metadata.get('revision', 'Not specified')}</p>
  </div>

  <div class="edit-note"><strong>Note:</strong> This report contains design criteria reviewed/edited by the user.</div>
"""
        
        if load_diagrams:
            html += """
  <div class="note">
    <strong>Note:</strong> This document contains load diagrams and tables. 
    This indicates that relevant diagrams/tables can be found on the specified page in the original drawing.
  </div>
"""
        
        html += f"""
  <h2>Final Design Criteria</h2>
  <div class="criteria">{edited_criteria}</div>
</body>
</html>
"""
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(f"Final Design Criteria Report\nDocument: {original_filename}\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nStatus: User-Edited Content\n")
            f.write("="*50 + "\n\nFINAL DESIGN CRITERIA:\n")
            f.write(edited_criteria or "")

        json_filename = f"final_design_criteria_asset_payload_{session_id}.json"
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
        payload = build_assetguard_create_asset_payload(edited_criteria, original_filename, metadata)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        meta.update({
            "session_id": session_id,
            "status": "final",
            "original_filename": original_filename,
            "artifacts": {
                "pdf": os.path.exists(pdf_path),
                "html": os.path.exists(html_path),
                "text": os.path.exists(text_path),
                "json": os.path.exists(json_path)
            },
            "final_generated_at": datetime.now().isoformat()
        })
        save_meta(session_id, meta)

        return jsonify({
            "success": True,
            "pdf_report_url": f"/uploads/{pdf_filename}" if os.path.exists(pdf_path) else None,
            "html_report_url": f"/uploads/{html_filename}",
            "json_download_url": f"/uploads/{json_filename}",
            "text_download_url": f"/uploads/{text_filename}",
            "generated_at": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error generating final report: {str(e)}")
        return jsonify({"error": f"Failed to generate final report: {str(e)}"}), 500

# ---------- Gemini final (kept) ----------
@app.route('/api/generate-final-report-gemini', methods=['POST'])
def generate_final_report_gemini():
    try:
        data = request.get_json() or {}
        if 'design_criteria' not in data:
            return jsonify({"error": "No design criteria provided"}), 400

        edited_criteria = data['design_criteria']
        original_filename = data.get('original_filename', 'document.pdf')
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400

        # Extract metadata from edited criteria
        metadata = extract_metadata_from_text(edited_criteria)

        # RE-DETECT load diagrams from session metadata
        load_diagrams = []
        meta = load_meta(session_id)
        if meta.get('load_diagrams'):
            load_diagrams = meta['load_diagrams']
            print(f"[Gemini Final Report] Restored {len(load_diagrams)} diagram references from metadata")
        
        # Re-annotate the edited criteria
        if load_diagrams:
            print(f"[Gemini Final Report] Re-annotating edited criteria with diagram references...")
            edited_criteria = annotate_design_criteria_with_diagrams(edited_criteria, load_diagrams)

        pdf_filename  = f"design_criteria_report_{session_id}.pdf"
        pdf_path      = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        html_filename = f"design_criteria_report_{session_id}.html"
        html_path     = os.path.join(app.config['UPLOAD_FOLDER'], html_filename)
        text_filename = f"final_design_criteria_{session_id}.txt"
        text_path     = os.path.join(app.config['UPLOAD_FOLDER'], text_filename)


        pdf_ok = generate_pdf_with_load_images(edited_criteria, [], filename=original_filename, output_path=pdf_path, metadata=metadata)
        
        project_title = metadata.get('project', original_filename.replace('.pdf', '').replace('_', ' '))

        html = f"""<!DOCTYPE html>
<html>
<head>
  <title>Final Design Criteria Report (Gemini) - {original_filename}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin:20px; line-height:1.6; }}
    .header {{ background:#f4f4f4; padding:20px; border-radius:5px; margin-bottom:20px; }}
    .metadata {{ background: #e8f4f8; padding: 10px; border-radius: 3px; margin-bottom: 20px; }}
    .note {{ background:#d4edda; padding:10px; border-left:4px solid #28a745; border-radius:5px; margin-bottom: 15px; }}
    .info-note {{ background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0; border-radius: 5px; }}
    .criteria {{ background:#f9f9f9; padding:15px; border-left:4px solid #007acc; white-space:pre-wrap; font-family: monospace; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>Final Engineering Design Criteria Report (Gemini)</h1>
    <p><strong>Document:</strong> {original_filename}</p>
    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>Status:</strong> User-Edited Content</p>
  </div>

  <div class="metadata">
    <h3>Document Information</h3>
    <p><strong>Drawing Number:</strong> {metadata.get('drawing_number', 'Not specified')}</p>
    <p><strong>Project:</strong> {project_title}</p>
    <p><strong>Date:</strong> {metadata.get('date', 'Not specified')}</p>
    <p><strong>Revision:</strong> {metadata.get('revision', 'Not specified')}</p>
  </div>

  <div class="note"><strong>Note:</strong> This report contains design criteria reviewed/edited by the user.</div>
"""
        
        if load_diagrams:
            html += """
  <div class="info-note">
    <strong>Note:</strong> This document contains load diagrams and tables. 
    This indicates that relevant diagrams/tables can be found on the specified page in the original drawing.
  </div>
"""
        
        html += f"""
  <h2>Final Design Criteria</h2>
  <div class="criteria">{edited_criteria}</div>
</body>
</html>"""
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
            
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write("Final Design Criteria Report (Gemini)\n")
            f.write(f"Document: {original_filename}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*50 + "\n\n")
            f.write(edited_criteria or "")

        json_filename = f"final_design_criteria_asset_payload_{session_id}.json"
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
        payload = build_assetguard_create_asset_payload(edited_criteria, original_filename, metadata)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        meta.update({
            "session_id": session_id,
            "status": "final",
            "engine": "Gemini",
            "original_filename": original_filename,
            "artifacts": {
                "pdf": os.path.exists(pdf_path),
                "html": os.path.exists(html_path),
                "text": os.path.exists(text_path),
                "json": os.path.exists(json_path)
            },
            "final_generated_at": datetime.now().isoformat()
        })
        save_meta(session_id, meta)

        return jsonify({
            "success": True,
            "engine": "gemini",
            "pdf_report_url": f"/uploads/{pdf_filename}" if os.path.exists(pdf_path) else None,
            "html_report_url": f"/uploads/{html_filename}",
            "json_download_url": f"/uploads/{json_filename}",
            "text_download_url": f"/uploads/{text_filename}",
            "generated_at": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[Gemini Final] Error: {e}")
        return jsonify({"error": f"Failed to generate final Gemini report: {str(e)}"}), 500

# ---------- Static & root ----------
@app.route('/uploads/<path:filename>')
def download_file(filename):
    # served inline; the UI uses these for <img> thumbnails
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

def _are_sessions_related(group1, group2):
    # Relationship detection disabled; sessions shown separately
    return False

def _merge_session_groups(groups):
    # (unchanged utility; kept for future)
    if not groups:
        return {}
    groups.sort(key=lambda g: g['earliest_generated'])
    base_group = groups[0]
    for group in groups:
        project_title = group.get('project_title', '')
        if project_title and ('project' in project_title.lower() or len(project_title) > len(base_group.get('project_title', ''))):
            base_group = group
            break
    merged = base_group.copy()
    all_reports, all_session_files, all_session_dirs, all_original_files, processing_attempts = [], [], set(), set(), []
    for i, group in enumerate(groups):
        for report in group['reports']:
            rc = report.copy()
            rc['processing_attempt'] = i + 1
            rc['attempt_engine'] = 'Gemini' if 'gemini' in group['session_id'] else 'GPT'
            rc['attempt_session_id'] = group['session_id']
            all_reports.append(rc)
        if group['session_files']:
            all_session_files.extend(group['session_files'])
        if group['session_directory']:
            all_session_dirs.add(group['session_directory'])
        if group.get('original_file_url'):
            all_original_files.add(group['original_file_url'])
        processing_attempts.append({
            'session_id': group['session_id'],
            'engine': 'Gemini' if 'gemini' in group['session_id'] else 'GPT',
            'generated_at': group['earliest_generated'],
            'success': any(r.get('design_criteria', '') != 'Design criteria not available' for r in group['reports'])
        })
    best_title = merged.get('project_title', '')
    for group in groups:
        title = group.get('project_title', '')
        if title and (len(title) > len(best_title) or 'project' in title.lower()):
            best_title = title
    best_filename = merged.get('original_filename', '')
    for group in groups:
        filename = group.get('original_filename', '')
        if filename and len(filename) > len(best_filename):
            best_filename = filename
    merged['reports'] = sorted(all_reports, key=lambda r: (r['processing_attempt'], r['generated_at']))
    merged['session_files'] = all_session_files
    merged['session_directory'] = list(all_session_dirs)[0] if all_session_dirs else None
    merged['processing_attempts'] = processing_attempts
    merged['project_title'] = best_title
    merged['original_filename'] = best_filename
    merged['original_file_url'] = list(all_original_files)[0] if all_original_files else None
    all_times = [report['generated_at'] for report in all_reports]
    merged['earliest_generated'] = min(all_times)
    merged['latest_generated'] = max(all_times)
    merged['session_id'] = f"project_{hash(best_title) % 10000:04d}"
    merged['is_merged'] = True
    merged['attempt_count'] = len(groups)
    print(f"Merged {len(groups)} sessions into project: '{best_title}' with {len(all_reports)} total reports")
    return merged

if __name__ == '__main__':
    app.run(debug=True)
