from openai import OpenAI
import json
import os
import base64
from datetime import datetime
import numpy as np
from PIL import Image
import re
from dotenv import load_dotenv  # 加这行


load_dotenv()  # Load env variables from .env (call before OpenAI init)


client = OpenAI()

def extract_design_criteria(text, filename):
    """Extract ONLY design criteria sections from OCR text using OpenAI API"""
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
- Location: [Exact site/berth/location name if shown in title block, header, or notes]
- Date: [First check bottom right corner box, then check revision history bottom left]
- Revision: [If found]

Document filename: {filename}

TEXT:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    return response.choices[0].message.content



def extract_metadata_from_text(design_criteria_text):
    """Extract metadata from the design criteria text"""
    metadata = {
        'drawing_number': 'Not specified',
        'project': 'Not specified',
        'location': 'Not specified',
        'date': 'Not specified',
        'revision': 'Not specified'
    }
    
    lines = design_criteria_text.split('\n')
    in_metadata = False
    
    for line in lines:
        if 'METADATA:' in line:
            in_metadata = True
            continue
        if in_metadata:
            if 'Drawing Number:' in line:
                metadata['drawing_number'] = line.split(':', 1)[1].strip()
            elif 'Project:' in line:
                metadata['project'] = line.split(':', 1)[1].strip()
            elif 'Location:' in line:
                metadata['location'] = line.split(':', 1)[1].strip()
            elif 'Date:' in line:
                metadata['date'] = line.split(':', 1)[1].strip()
            elif 'Revision:' in line:
                metadata['revision'] = line.split(':', 1)[1].strip()
    
    return metadata

def extract_load_diagram_regions(image_path, design_criteria_text):
    """Extract regions containing load diagrams from engineering drawings"""
    print(f"[DEBUG - FUNCTION ENTRY] extract_load_diagram_regions called with: {image_path}")
    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        vision_prompt = f"""
You are analyzing an engineering drawing to find load diagrams and design criteria illustrations.

LOOK FOR these specific visual elements:
1. Vehicle/truck diagrams showing wheel positions and axle spacing
2. Diagrams with measurements between wheels (distances in meters or feet)
3. Load values shown on diagrams (tonnes, kN, kPa, kg)
4. Tables or boxes containing design load specifications
5. Force arrows or load distribution illustrations
6. Railway/locomotive load diagrams
7. Crane load configurations
8. Any schematic showing weight distribution

DESIGN CRITERIA EXTRACTED FROM THIS DRAWING:
{design_criteria_text[:500]}

CRITICAL INSTRUCTIONS:
- If you find ANY load-related diagrams, tables, or illustrations, return their locations
- Return coordinates as percentages (0-100) of the full image: x1,y1,x2,y2
- x1,y1 = top-left corner, x2,y2 = bottom-right corner
- Include some padding around the diagram (add ~2-5% margin)
- If you find NOTHING relevant, respond with exactly: NO_LOAD_DIAGRAMS

REQUIRED OUTPUT FORMAT (use this exact format):
DIAGRAM: Vehicle axle load configuration showing 4 wheels
COORDINATES: 15,45,85,75
RELEVANCE: Shows the wheel spacing and axle loads mentioned in design criteria

DIAGRAM: Design load table with kPa values
COORDINATES: 10,20,45,40
RELEVANCE: Contains the deck load specifications

Now analyze the image and respond:
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": vision_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1200,
            temperature=0
        )
        
        analysis_result = response.choices[0].message.content or ""
        print(f"[DEBUG] Vision API response:\n{analysis_result}\n")
        
        if "NO_LOAD_DIAGRAMS" in analysis_result.upper():
            print("[DEBUG] No load diagrams found by Vision API")
            return []
            
        diagrams = []

        # Try to parse DIAGRAM: blocks
        if "DIAGRAM:" in analysis_result:
            section_blocks = analysis_result.split("DIAGRAM:")
            
            for idx, block in enumerate(section_blocks[1:], 1):
                try:
                    lines = block.strip().split('\n')
                    description = lines[0].strip()
                    
                    coordinates_line = None
                    relevance = ""
                    
                    for line in lines:
                        line_upper = line.upper()
                        if "COORDINATES:" in line_upper or "COORDINATE:" in line_upper:
                            # Extract the part after the colon
                            parts = line.split(":", 1)
                            if len(parts) > 1:
                                coordinates_line = parts[1].strip()
                        elif "RELEVANCE:" in line_upper:
                            parts = line.split(":", 1)
                            if len(parts) > 1:
                                relevance = parts[1].strip()
                    
                    if coordinates_line:
                        # Extract numbers from the coordinates line
                        import re
                        numbers = re.findall(r'\d+\.?\d*', coordinates_line)
                        if len(numbers) >= 4:
                            coords = [float(numbers[i]) for i in range(4)]
                            
                            # Validate coordinates are within bounds
                            if all(0 <= c <= 100 for c in coords) and coords[2] > coords[0] and coords[3] > coords[1]:
                                diagrams.append({
                                    'description': description,
                                    'coordinates': coords,
                                    'relevance': relevance or description,
                                    'type': 'load_diagram'
                                })
                                print(f"[DEBUG] ✓ Found diagram #{idx}: {description[:50]}... at {coords}")
                            else:
                                print(f"[DEBUG] ✗ Invalid coordinates for diagram #{idx}: {coords}")
                        else:
                            print(f"[DEBUG] ✗ Not enough coordinate values in: {coordinates_line}")
                    else:
                        print(f"[DEBUG] ✗ No coordinates found in diagram block #{idx}")

                except Exception as e:
                    print(f"[DEBUG] ✗ Error parsing diagram block #{idx}: {e}")
                    continue
        else:
            print("[DEBUG] No 'DIAGRAM:' markers found in response")
        
        # Fallback: If no diagrams found but response looks positive, try different parsing
        if not diagrams and "NO_LOAD_DIAGRAMS" not in analysis_result.upper():
            print("[DEBUG] Attempting fallback parsing...")
            # Look for any coordinate patterns in the response
            import re
            coord_pattern = r'(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)'
            matches = re.findall(coord_pattern, analysis_result)
            
            for idx, match in enumerate(matches, 1):
                try:
                    coords = [float(x) for x in match]
                    if all(0 <= c <= 100 for c in coords) and coords[2] > coords[0] and coords[3] > coords[1]:
                        diagrams.append({
                            'description': f'Load diagram {idx} (auto-detected)',
                            'coordinates': coords,
                            'relevance': 'Load-related diagram identified in drawing',
                            'type': 'load_diagram'
                        })
                        print(f"[DEBUG] ✓ Fallback found diagram #{idx} at {coords}")
                except:
                    continue
        
        if not diagrams:
            print("[DEBUG] ⚠ No load diagrams could be extracted from Vision API response")
        else:
            print(f"[DEBUG] ✓✓✓ Successfully extracted {len(diagrams)} load diagram(s)")

        return diagrams
        
    except Exception as e:
        print(f"[ERROR] Exception in extract_load_diagram_regions: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def extract_relevant_image_sections(image_path, design_criteria_text):
    """Use OpenAI Vision to identify and crop relevant sections of engineering drawings"""
    try:
        # Read the image
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Analyze the image with GPT-4 Vision to find relevant sections
        vision_prompt = f"""
Analyze this engineering drawing IMAGE and find rectangular regions that directly support the extracted design criteria below.

DESIGN CRITERIA TO MATCH:
{design_criteria_text}

COORDINATE SYSTEM
- Use whole-image percentage coordinates:
  (0,0) = top-left; (100,100) = bottom-right
- Return boxes as: x1,y1,x2,y2  (integers or one decimal; 0–100)

WHAT TO SELECT
- Tables of specifications, dimension callouts, material notes, load notes, connection details, standards/codes callouts that clearly evidence or illustrate the criteria text.
- Prefer concise, high-signal regions (avoid huge boxes unless the whole page is necessary).

WHAT TO EXCLUDE
- Title blocks, legends, scales, sheet indices, decorative symbols, or anything unrelated to the criteria.

IF NOTHING MATCHES
- Return exactly: NO_RELEVANT_SECTIONS

RESPONSE FORMAT (repeat blocks as needed; no extra commentary):
SECTION: [Short description of the technical info shown]
COORDINATES: x1,y1,x2,y2
RELEVANCE: [Why this region supports/matches a specific extracted item]

SECTION: [Description]
COORDINATES: x1,y1,x2,y2
RELEVANCE: [Why relevant]
"""

        response = client.chat.completions.create(
            model="gpt-4o",  # Updated to use gpt-4o which supports vision
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": vision_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        analysis_result = response.choices[0].message.content
        
        if "NO_RELEVANT_SECTIONS" in analysis_result:
            return []
        
        # Parse the response to extract sections
        sections = []
        section_blocks = analysis_result.split("SECTION:")
        
        for block in section_blocks[1:]:  # Skip first empty element
            try:
                lines = block.strip().split('\n')
                description = lines[0].strip()
                
                # Find coordinates line
                coordinates_line = None
                relevance = ""
                for line in lines:
                    if line.startswith("COORDINATES:"):
                        coordinates_line = line.replace("COORDINATES:", "").strip()
                    elif line.startswith("RELEVANCE:"):
                        relevance = line.replace("RELEVANCE:", "").strip()
                
                if coordinates_line:
                    # Parse coordinates
                    coords = [float(x.strip()) for x in coordinates_line.split(',')]
                    if len(coords) == 4:
                        sections.append({
                            'description': description,
                            'coordinates': coords,
                            'relevance': relevance
                        })
            except:
                continue
        
        return sections
        
    except Exception as e:
        print(f"Error analyzing image sections: {str(e)}")
        return []

def crop_image_sections(image_path, sections, output_dir):
    """Crop specific sections from an image based on coordinates"""
    try:
        # Open the image
        img = Image.open(image_path)
        img_width, img_height = img.size
        
        cropped_sections = []
        
        for i, section in enumerate(sections):
            try:
                # Convert percentage coordinates to pixel coordinates
                x1 = int((section['coordinates'][0] / 100) * img_width)
                y1 = int((section['coordinates'][1] / 100) * img_height)
                x2 = int((section['coordinates'][2] / 100) * img_width)
                y2 = int((section['coordinates'][3] / 100) * img_height)
                
                # Ensure coordinates are within image bounds
                x1 = max(0, min(x1, img_width))
                y1 = max(0, min(y1, img_height))
                x2 = max(x1 + 50, min(x2, img_width))  # Minimum 50px width
                y2 = max(y1 + 50, min(y2, img_height))  # Minimum 50px height
                
                # Crop the section
                cropped = img.crop((x1, y1, x2, y2))
                
                # Save the cropped section
                crop_filename = f"load_diagram_{i+1}.png"
                crop_path = os.path.join(output_dir, crop_filename)
                cropped.save(crop_path)
                
                cropped_sections.append({
                    'path': crop_path,
                    'description': section['description'],
                    'relevance': section['relevance'],
                    'original_coordinates': section['coordinates']
                })
                
            except Exception as e:
                print(f"Error cropping section {i}: {str(e)}")
                continue
        
        return cropped_sections
        
    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return []

def analyze_relevant_images_with_cropping(design_criteria, image_paths, output_dir):
    """Analyze images and extract relevant sections"""
    if not image_paths:
        return []
    
    # Create directory for cropped sections
    crops_dir = os.path.join(output_dir, "cropped_sections")
    os.makedirs(crops_dir, exist_ok=True)
    
    all_relevant_sections = []
    
    for image_path in image_paths:
        if not os.path.exists(image_path):
            continue
            
        page_num = extract_page_number_from_path(image_path)
        print(f"   🔍 Analyzing page {page_num} for relevant sections...")
        
        # Check if this page is mentioned in design criteria
        page_mentioned = f"PAGE {page_num}" in design_criteria.upper()
        
        if page_mentioned or page_num <= 3:  # Analyze first 3 pages and mentioned pages
            # Use GPT-4 Vision to identify relevant sections
            sections = extract_relevant_image_sections(image_path, design_criteria)
            
            if sections:
                print(f"   📷 Found {len(sections)} relevant sections on page {page_num}")
                # Crop the relevant sections
                cropped_sections = crop_image_sections(image_path, sections, crops_dir)
                
                for section in cropped_sections:
                    section['page'] = page_num
                    section['original_image'] = image_path
                    all_relevant_sections.append(section)
            else:
                print(f"   ⚪ No specific relevant sections found on page {page_num}")
    
    return all_relevant_sections

def parse_design_criteria_into_sections(design_criteria_text):
    """Parse the design criteria text into structured sections"""
    sections = {}
    current_item = None
    current_content = []
    
    lines = design_criteria_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('ITEM:'):
            # Save previous item
            if current_item:
                sections[current_item] = '\n'.join(current_content)
            
            # Start new item
            current_item = line
            current_content = []
        elif line.startswith('METADATA:'):
            # Save previous item
            if current_item:
                sections[current_item] = '\n'.join(current_content)
            
            # Start metadata section
            current_item = 'METADATA'
            current_content = []
        elif line and current_item:
            current_content.append(line)
    
    # Save last item
    if current_item:
        sections[current_item] = '\n'.join(current_content)
    
    return sections

def match_images_to_criteria_sections(design_criteria_text, relevant_sections):
    """Match cropped image sections to specific design criteria items"""
    criteria_sections = parse_design_criteria_into_sections(design_criteria_text)
    
    matched_sections = {}
    
    for criteria_item, criteria_content in criteria_sections.items():
        if criteria_item == 'METADATA':
            continue
            
        matched_sections[criteria_item] = {
            'content': criteria_content,
            'images': []
        }
        
        # Find images that match this criteria section
        for img_section in relevant_sections:
            # Simple keyword matching - could be enhanced with more sophisticated NLP
            criteria_keywords = set(re.findall(r'\b\w+\b', criteria_content.lower()))
            img_keywords = set(re.findall(r'\b\w+\b', 
                                        (img_section['description'] + ' ' + img_section['relevance']).lower()))
            
            # Check for keyword overlap or if the image relevance mentions key terms
            overlap = len(criteria_keywords.intersection(img_keywords))
            
            # Also check for specific technical terms
            key_terms = ['steel', 'load', 'pile', 'grating', 'handrail', 'coating', 'weld', 'bolt']
            criteria_has_term = any(term in criteria_content.lower() for term in key_terms)
            img_has_term = any(term in (img_section['description'] + ' ' + img_section['relevance']).lower() 
                             for term in key_terms)
            
            if overlap > 2 or (criteria_has_term and img_has_term):
                matched_sections[criteria_item]['images'].append(img_section)
    
    return matched_sections

def encode_image_to_base64(image_path):
    """Convert image to base64 for HTML embedding"""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
    except Exception as e:
        print(f"Error encoding image {image_path}: {str(e)}")
        return None

def extract_page_number_from_path(image_path):
    """Extract page number from image path like 'page_1.png'"""
    try:
        filename = os.path.basename(image_path)
        # Extract number from filename like 'page_1.png'
        import re
        match = re.search(r'page_(\d+)', filename)
        if match:
            return int(match.group(1))
    except:
        pass
    return 1

def process_document_directory(dir_path):
    """Process all JSON files in a directory as a single multi-page document"""
    try:
        # Get all JSON files in the directory and sort them
        json_files = sorted([f for f in os.listdir(dir_path) if f.endswith('.json')])
        
        if not json_files:
            return f"No JSON files found in {dir_path}"
        
        # Extract document name from directory
        document_name = os.path.basename(dir_path)
        
        # Check for images directory
        images_dir = os.path.join(dir_path, "images")
        image_paths = []
        if os.path.exists(images_dir):
            image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            image_paths = [os.path.join(images_dir, img) for img in sorted(image_files)]
        
        # Also check for image_paths.txt file
        image_paths_file = os.path.join(dir_path, "image_paths.txt")
        if os.path.exists(image_paths_file):
            with open(image_paths_file, 'r') as f:
                additional_paths = [line.strip() for line in f.readlines() if line.strip()]
                # Verify paths exist
                additional_paths = [p for p in additional_paths if os.path.exists(p)]
                image_paths.extend(additional_paths)
        
        # Combine text from all pages
        combined_text = []
        page_info = []
        
        for json_file in json_files:
            json_path = os.path.join(dir_path, json_file)
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract text from OCR results
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
        
        # Combine all page texts
        full_document_text = "\n\n".join(combined_text)
        
        # Extract design criteria using OpenAI
        print(f"   🤖 Analyzing {document_name} with GPT...")
        design_criteria = extract_design_criteria(full_document_text, document_name)
        
        # Analyze images and extract relevant sections
        print(f"   🖼️ Analyzing images for relevant sections...")
        relevant_sections = analyze_relevant_images_with_cropping(design_criteria, image_paths, dir_path)
        
        # Match images to specific criteria sections
        matched_sections = match_images_to_criteria_sections(design_criteria, relevant_sections)
        
        return {
            'document_name': document_name,
            'design_criteria': design_criteria,
            'pages_processed': len(page_info),
            'page_info': page_info,
            'total_images': len(image_paths),
            'relevant_sections': relevant_sections,
            'matched_sections': matched_sections,
            'processed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return f"Error processing document directory {dir_path}: {str(e)}"

def generate_html_report(results, output_folder="design_criteria_output"):
    """Generate HTML reports with embedded relevant image sections"""
    os.makedirs(output_folder, exist_ok=True)
    
    # Generate summary HTML
    summary_file = os.path.join(output_folder, "summary_report.html")
    
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Engineering Design Criteria Extraction Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { background-color: #f4f4f4; padding: 20px; border-radius: 5px; }
        .document-section { margin: 30px 0; border: 1px solid #ddd; padding: 20px; border-radius: 5px; }
        .criteria-item { margin: 20px 0; padding: 15px; border: 1px solid #e0e0e0; border-radius: 5px; }
        .criteria-content { background-color: #f9f9f9; padding: 15px; border-left: 4px solid #007acc; margin: 10px 0; }
        .image-section { margin: 15px 0; display: flex; flex-wrap: wrap; gap: 15px; }
        .image-item { flex: 1; min-width: 300px; max-width: 500px; }
        .section-image { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 3px; }
        .image-caption { font-style: italic; color: #666; font-size: 0.85em; margin-top: 5px; padding: 5px; background-color: #f5f5f5; border-radius: 3px; }
        .metadata { background-color: #e8f4f8; padding: 10px; border-radius: 3px; font-size: 0.9em; }
        .error { color: #d32f2f; }
        .success { color: #388e3c; }
        .item-title { color: #1976d2; font-weight: bold; font-size: 1.1em; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏗️ Engineering Design Criteria Extraction Report</h1>
        <p><strong>Generated:</strong> """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        <p><strong>Total Documents Processed:</strong> """ + str(len(results)) + """</p>
    </div>
"""
    
    for dir_path, result in results.items():
        document_name = os.path.basename(dir_path)
        
        html_content += f"""
    <div class="document-section">
        <h2>📄 {document_name}</h2>
"""
        
        if isinstance(result, dict):
            # Success case
            html_content += f"""
        <div class="metadata">
            <strong>Status:</strong> <span class="success">✓ Successfully processed</span><br>
            <strong>Pages:</strong> {result.get('pages_processed', 'Unknown')}<br>
            <strong>Images Found:</strong> {result.get('total_images', 0)}<br>
            <strong>Relevant Sections:</strong> {len(result.get('relevant_sections', []))}<br>
            <strong>Processed:</strong> {result.get('processed_at', 'Unknown')}
        </div>
"""
            
            # Display matched sections (criteria with relevant images)
            matched_sections = result.get('matched_sections', {})
            if matched_sections:
                for criteria_item, section_data in matched_sections.items():
                    if section_data['images']:  # Only show items that have relevant images
                        html_content += f"""
        <div class="criteria-item">
            <div class="item-title">{criteria_item}</div>
            <div class="criteria-content">
                <pre>{section_data['content']}</pre>
            </div>
"""
                        
                        if section_data['images']:
                            html_content += """
            <div class="image-section">
"""
                            for img_section in section_data['images']:
                                if os.path.exists(img_section['path']):
                                    encoded_image = encode_image_to_base64(img_section['path'])
                                    if encoded_image:
                                        file_ext = os.path.splitext(img_section['path'])[1].lower()[1:]
                                        html_content += f"""
                <div class="image-item">
                    <img src="data:image/{file_ext};base64,{encoded_image}" class="section-image" alt="{img_section['description']}">
                    <div class="image-caption">
                        <strong>Page {img_section['page']}:</strong> {img_section['description']}<br>
                        <em>{img_section['relevance']}</em>
                    </div>
                </div>
"""
                            html_content += "            </div>"
                        
                        html_content += "        </div>"
            
            # Show remaining criteria without images
            remaining_criteria = result.get('design_criteria', '')
            html_content += f"""
        <h3>📋 Complete Design Criteria</h3>
        <div class="criteria-content">
            <pre>{remaining_criteria}</pre>
        </div>
"""
        else:
            # Error case
            html_content += f"""
        <div class="metadata">
            <strong>Status:</strong> <span class="error">✗ Processing failed</span>
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
    
    # Save summary HTML
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Generate individual HTML files for each document
    for dir_path, result in results.items():
        if isinstance(result, dict):
            document_name = os.path.basename(dir_path)
            individual_file = os.path.join(output_folder, f"document_{document_name}.html")
            
            # Use same structure as summary but for single document
            individual_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Design Criteria - {document_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
        .criteria-item {{ margin: 20px 0; padding: 15px; border: 1px solid #e0e0e0; border-radius: 5px; }}
        .criteria-content {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #007acc; margin: 10px 0; }}
        .image-section {{ margin: 15px 0; display: flex; flex-wrap: wrap; gap: 15px; }}
        .image-item {{ flex: 1; min-width: 300px; max-width: 500px; }}
        .section-image {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 3px; }}
        .image-caption {{ font-style: italic; color: #666; font-size: 0.85em; margin-top: 5px; padding: 5px; background-color: #f5f5f5; border-radius: 3px; }}
        .item-title {{ color: #1976d2; font-weight: bold; font-size: 1.1em; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏗️ {document_name}</h1>
        <p><strong>Pages Processed:</strong> {result.get('pages_processed', 'Unknown')}</p>
        <p><strong>Generated:</strong> {result.get('processed_at', 'Unknown')}</p>
    </div>
"""
            
            # Add matched sections for individual document
            matched_sections = result.get('matched_sections', {})
            if matched_sections:
                for criteria_item, section_data in matched_sections.items():
                    if section_data['images']:
                        individual_html += f"""
    <div class="criteria-item">
        <div class="item-title">{criteria_item}</div>
        <div class="criteria-content">
            <pre>{section_data['content']}</pre>
        </div>
"""
                        
                        if section_data['images']:
                            individual_html += """
        <div class="image-section">
"""
                            for img_section in section_data['images']:
                                if os.path.exists(img_section['path']):
                                    encoded_image = encode_image_to_base64(img_section['path'])
                                    if encoded_image:
                                        file_ext = os.path.splitext(img_section['path'])[1].lower()[1:]
                                        individual_html += f"""
            <div class="image-item">
                <img src="data:image/{file_ext};base64,{encoded_image}" class="section-image" alt="{img_section['description']}">
                <div class="image-caption">
                    <strong>Page {img_section['page']}:</strong> {img_section['description']}<br>
                    <em>{img_section['relevance']}</em>
                </div>
            </div>
"""
                            individual_html += "        </div>"
                        
                        individual_html += "    </div>"
            
            # Complete criteria
            individual_html += f"""
    <h2>📋 Complete Design Criteria</h2>
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

def save_results_to_file(results, output_folder="design_criteria_output"):
    """Save results to both text and HTML formats"""
    os.makedirs(output_folder, exist_ok=True)
    
    # Generate HTML reports with cropped images
    generate_html_report(results, output_folder)
    
    # Also save text summary for backward compatibility
    summary_file = os.path.join(output_folder, "extraction_summary.txt")
    with open(summary_file, "w", encoding='utf-8') as f:
        f.write("Design Criteria Extraction Summary\n")
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
                f.write(f"Images: {result.get('total_images', 0)} total, {len(result.get('relevant_sections', []))} relevant sections\n")
                f.write(f"Processed: {result.get('processed_at', 'Unknown')}\n\n")
                f.write("Design Criteria:\n")
                f.write(result.get('design_criteria', 'No criteria extracted'))
            else:
                f.write(f"Status: Failed\n")
                f.write(f"Error: {result}\n")
            
            f.write("\n" + "=" * 50 + "\n")
    
    # Save individual text files for each document
    for dir_path, result in results.items():
        if isinstance(result, dict):
            document_name = os.path.basename(dir_path)
            individual_file = os.path.join(output_folder, f"document_{document_name}.txt")
            
            with open(individual_file, "w", encoding='utf-8') as f:
                f.write(f"Design Criteria Extraction - {document_name}\n")
                f.write("=" * 50 + "\n")
                f.write(f"Pages processed: {result.get('pages_processed', 'Unknown')}\n")
                f.write(f"Images found: {result.get('total_images', 0)}\n")
                f.write(f"Relevant sections: {len(result.get('relevant_sections', []))}\n")
                f.write(f"Processed: {result.get('processed_at', 'Unknown')}\n\n")
                f.write("DESIGN CRITERIA:\n")
                f.write("-" * 20 + "\n")
                f.write(result.get('design_criteria', 'No criteria extracted'))

def main():
    # Find all output directories
    output_directories = []
    
    # Search for output directories
    for output_dir in ['output1', 'output2', 'output3', 'output4', 'output5', 'output6','output7','output8','output9','output10','output11','output12']:
        dir_path = f"./ocr_results/{output_dir}"
        if os.path.exists(dir_path):
            output_directories.append(dir_path)
    
    if not output_directories:
        print("No output directories found in ocr_results")
        return
    
    print(f"Found {len(output_directories)} documents to process")
    
    results = {}
    
    # Process each document directory
    for i, dir_path in enumerate(output_directories, 1):
        document_name = os.path.basename(dir_path)
        print(f"Processing document {i}/{len(output_directories)}: {document_name}")
        
        try:
            result = process_document_directory(dir_path)
            results[dir_path] = result
            print(f"✓ Completed: {document_name}")
        except Exception as e:
            error_msg = f"Error processing document {dir_path}: {str(e)}"
            results[dir_path] = error_msg
            print(f"✗ Failed: {document_name} - {str(e)}")
    
    # Save all results in both text and HTML formats
    save_results_to_file(results)
    
    print("\nProcessing complete!")
    print(f"Processed {len(results)} documents")
    print("📄 Text summaries saved to design_criteria_output/")
    print("🌐 HTML reports with relevant image sections saved to design_criteria_output/")
    print("📊 Open summary_report.html in your browser to view results with cropped relevant sections!")

if __name__ == "__main__":
    main()