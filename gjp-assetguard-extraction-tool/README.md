# Capstone-Project-Sem-2-2025

## Engineering Document Analysis with AI

This application extracts design criteria and field data from engineering drawings and documents using Google Cloud Vision API combined with OpenAI GPT or Google Gemini.
It includes a web interface with advanced batch processing, real-time progress tracking, and interactive report editing.

## Prerequisites

Before running the application, you need:
- Google Cloud Platform (GCP) account with Vision API enabled
- OpenAI API account (for GPT) (Optional, can be done with just Gemini key)
- Google Gemini API key (for Gemini)
- Python 3.8 or higher


## Environment Variable Requirements

**The application requires the following environment variables to be set (either in your shell or in a `.env` file in the project root):**

- `GOOGLE_APPLICATION_CREDENTIALS` — Path to your GCP service account JSON key file  
  *(Example: `GOOGLE_APPLICATION_CREDENTIALS=./model-night-467712-a8-5e7e79593d88.json`)*

- `GCP_BUCKET_NAME` — Name of your Google Cloud Storage bucket  
  *(Example: `GCP_BUCKET_NAME=testing-bucket-ocr-uwa`)*

- GEMINI_API_KEY — Your Gemini API key

**If any required variable is missing, the application will not start and will display an error.**

**Example `.env` file:**
```
GOOGLE_APPLICATION_CREDENTIALS=./model-night-467712-a8-5e7e79593d88.json
GCP_BUCKET_NAME=testing-bucket-ocr-uwa
GEMINI_API_KEY=xxxx
```

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/jksy1414/Capstone-Project-Sem-2-2025.git
cd Capstone-Project-Sem-2-2025
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create required directories
```bash
mkdir uploads
mkdir ocr_results
```

### 5. API Keys Setup

#### OpenAI GPT (Optional, only needed if you wish to use GPT model)
- This step is required as the OpenAI library uses the exported environment variable
- Get your API key from [OpenAI Platform](https://platform.openai.com/)
-  Set it as an environment variable:
    - macOS/Linux:
      ```bash
      export OPENAI_API_KEY=your_openai_api_key_here
      ```
    - Windows:
      ```cmd
      set OPENAI_API_KEY=your_openai_api_key_here
      ```

#### Google Gemini
- Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/)
- Please see "Environment Variable Requirements" for more information on setting Gemini API key.

#### GCP Vision
- Place your GCP service account JSON key file in the project root.
- You may need to change the credential JSON file name accordingly. The name to change is hte name of your full credential file.
- Set the credentials path in your environment or in `app.py`:
    ```python
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./your-key-file.json"
    ```

### 6. Run the application
```bash
python app.py
```
The application will be available at `http://localhost:5000`

## Usage

### Advanced Design Criteria Tab
- Upload PDFs or images (batch upload supported).
- Choose GPT or Gemini for analysis.
- Monitor extraction progress with the real-time progress bar.
- Edit extracted design criteria directly in the UI.
- Generate final reports (PDF/HTML/Text) linked with cropped drawing sections.

## Troubleshooting

- **API key not found:** Make sure your environment variables are set and restart your terminal.
- **Import errors:** Ensure your virtual environment is activated and run `pip install -r requirements.txt` again.
- **GCP credential errors:** Check your JSON key file location and filename.

### File Structure
```
Capstone-Project-Sem-2-2025/
├── app.py                  # Flask backend with API endpoints
├── gptapi.py               # GPT processing logic
├── geminiapi.py            # Gemini processing logic
├── progressTracker.py      # Progress bar and batch tracking
├── requirements.txt
├── templates/
│   └── index.html          # Web UI (Advanced + History tabs)
├── uploads/                # Uploaded files
└── ocr_results/            # OCR results and reports
```

## Features

- Multi-page PDF & image processing with Google Cloud Vision API
- AI-powered extraction (GPT or Gemini)
- Batch upload with weighted stage-based progress tracking
- Interactive web UI with tabs (Advanced, History)
- Relevant section cropping & embedding (GPT only)
- Downloadable reports (PDF, HTML, Text)
- Report history with search, delete, clear

## API Endpoints

### Document Processing

#### Batch Document Processing
**POST** `/api/process-batch-documents` — Process multiple PDFs/images with AI extraction

**Parameters**
| name    | type     | data type           | description                                         |
| ------- | -------- | ------------------- | --------------------------------------------------- |
| files[] | required | multipart/form-data | Array of PDF/image files to process                 |
| model   | optional | string              | AI model to use: "gpt" or "gemini" (default: "gpt") |

**Responses**
| http code | content-type     | response                                                                         |
| --------- | ---------------- | -------------------------------------------------------------------------------- |
| 200       | application/json | `{"success": true, "session_id": "...", "files_processed": 2, "results": [...]}` |
| 400       | application/json | `{"success": false, "error": "No files uploaded"}`                               |
| 500       | application/json | `{"success": false, "error": "Processing failed: ..."}`                          |

**Example cURL**
```bash
curl -X POST \
  -F "files[]=@document1.pdf" \
  -F "files[]=@drawing2.jpg" \
  -F "model=gpt" \
  http://localhost:5000/api/process-batch-documents
```

#### Single Document Processing
**POST** `/api/process-engineering-document` — Process single engineering document

**Parameters**
| name  | type     | data type           | description                                  |
| ----- | -------- | ------------------- | -------------------------------------------- |
| file  | required | multipart/form-data | PDF or image file to process                 |
| model | optional | string              | AI model: "gpt" or "gemini" (default: "gpt") |

**Responses**
| http code | content-type     | response                                                                                       |
| --------- | ---------------- | ---------------------------------------------------------------------------------------------- |
| 200       | application/json | `{"success": true, "filename": "...", "design_criteria": "...", "relevant_sections_count": 3}` |
| 400       | application/json | `{"success": false, "error": "Only PDF files are supported"}`                                  |
| 500       | application/json | `{"success": false, "error": "Processing failed"}`                                             |

**Example cURL**
```bash
curl -X POST \
  -F "file=@engineering_drawing.pdf" \
  -F "model=gemini" \
  http://localhost:5000/api/process-engineering-document
```

### Report Generation

#### Generate Final Report (GPT)
**POST** `/api/generate-final-report` — Generate final report with edited criteria (GPT pipeline)

**Parameters**
| name              | type     | data type          | description                        |
| ----------------- | -------- | ------------------ | ---------------------------------- |
| design_criteria   | required | string (JSON body) | Edited design criteria text        |
| session_id        | required | string (JSON body) | Session identifier from processing |
| original_filename | optional | string (JSON body) | Original document filename         |

**Responses**
| http code | content-type     | response                                                                                           |
| --------- | ---------------- | -------------------------------------------------------------------------------------------------- |
| 200       | application/json | `{"success": true, "pdf_report_url": "...", "html_report_url": "...", "text_download_url": "..."}` |
| 400       | application/json | `{"success": false, "error": "Missing required parameters"}`                                       |
| 500       | application/json | `{"success": false, "error": "Report generation failed"}`                                          |

**Example cURL**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"design_criteria": "Updated criteria text...", "session_id": "20241003_143022", "original_filename": "drawing.pdf"}' \
  http://localhost:5000/api/generate-final-report
```

#### Generate Final Report (Gemini)
**POST** `/api/generate-final-report-gemini` — Generate final report with edited criteria (Gemini pipeline)

**Parameters**
| name              | type     | data type          | description                        |
| ----------------- | -------- | ------------------ | ---------------------------------- |
| design_criteria   | required | string (JSON body) | Edited design criteria text        |
| session_id        | required | string (JSON body) | Session identifier from processing |
| original_filename | optional | string (JSON body) | Original document filename         |

**Responses**
| http code | content-type     | response                                                                                           |
| --------- | ---------------- | -------------------------------------------------------------------------------------------------- |
| 200       | application/json | `{"success": true, "pdf_report_url": "...", "html_report_url": "...", "text_download_url": "..."}` |
| 400       | application/json | `{"success": false, "error": "Missing required parameters"}`                                       |
| 500       | application/json | `{"success": false, "error": "Report generation failed"}`                                          |

### Progress Monitoring

#### Get Processing Status
**GET** `/api/process-status` — Get current processing progress

**Parameters**
| name | type | data type | description            |
| ---- | ---- | --------- | ---------------------- |
| None | N/A  | N/A       | No parameters required |

**Responses**
| http code | content-type     | response                                                                                     |
| --------- | ---------------- | -------------------------------------------------------------------------------------------- |
| 200       | application/json | `{"current_file": "document.pdf", "progress": 65, "stage": "AI Analysis", "total_files": 3}` |

**Example cURL**
```bash
curl -X GET http://localhost:5000/api/process-status
```

#### Reset Processing Status
**POST** `/api/process-status-reset` — Reset progress tracking

**Responses**
| http code | content-type     | response                                                      |
| --------- | ---------------- | ------------------------------------------------------------- |
| 200       | application/json | `{"success": true, "message": "Progress reset successfully"}` |

### Session Management

#### Get Previous Results
**GET** `/api/previous-results` — Retrieve processing history and previous sessions

**Responses**
| http code | content-type     | response                                                                                      |
| --------- | ---------------- | --------------------------------------------------------------------------------------------- |
| 200       | application/json | `{"sessions": [{"session_id": "...", "files": [...], "timestamp": "...", "reports": [...]}]}` |

**Example cURL**
```bash
curl -X GET http://localhost:5000/api/previous-results
```

#### Delete Specific Report
**POST** `/api/delete-report` — Delete a specific processing session

**Parameters**
| name       | type     | data type          | description                  |
| ---------- | -------- | ------------------ | ---------------------------- |
| session_id | required | string (JSON body) | Session identifier to delete |

**Responses**
| http code | content-type     | response                                                       |
| --------- | ---------------- | -------------------------------------------------------------- |
| 200       | application/json | `{"success": true, "message": "Session deleted successfully"}` |
| 400       | application/json | `{"success": false, "error": "Session ID not provided"}`       |
| 404       | application/json | `{"success": false, "error": "Session not found"}`             |

**Example cURL**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"session_id": "20241003_143022"}' \
  http://localhost:5000/api/delete-report
```

#### Clear All Previous Results
**POST** `/api/clear-previous-results` — Clear all processing history

**Responses**
| http code | content-type     | response                                                       |
| --------- | ---------------- | -------------------------------------------------------------- |
| 200       | application/json | `{"success": true, "message": "All previous results cleared"}` |
| 500       | application/json | `{"success": false, "error": "Failed to clear results"}`       |

**Example cURL**
```bash
curl -X POST http://localhost:5000/api/clear-previous-results
```

### File Downloads

#### Download Generated Files
**GET** `/uploads/{filename}` — Download uploaded files or generated reports

**Parameters**
| name     | type     | data type      | description              |
| -------- | -------- | -------------- | ------------------------ |
| filename | required | path parameter | Name of file to download |

**Responses**
| http code | content-type                           | response       |
| --------- | -------------------------------------- | -------------- |
| 200       | application/pdf, text/html, text/plain | File content   |
| 404       | text/html                              | File not found |

**Example cURL**
```bash
curl -X GET http://localhost:5000/uploads/design_criteria_report_20241003_143022.pdf --output report.pdf
```

### Error Codes

| Code | Description                                                 |
| ---- | ----------------------------------------------------------- |
| 200  | Success                                                     |
| 400  | Bad Request - Invalid parameters or missing required fields |
| 404  | Not Found - Requested resource does not exist               |
| 405  | Method Not Allowed - HTTP method not supported for endpoint |
| 413  | Payload Too Large - File size exceeds limit                 |
| 500  | Internal Server Error - Processing or server error          |

## Security Notes

- Keep your API keys secure and never commit them to version control
- The GCP JSON key file contains sensitive credentials, and can be used to perform actions on your cloud resources.
- Store secrets in .env or environment variables.
