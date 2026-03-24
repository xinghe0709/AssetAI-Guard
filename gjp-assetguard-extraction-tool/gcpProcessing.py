import os
import fitz  # PyMuPDF for PDF processing
from google.cloud import vision_v1
from google.cloud import storage
from dotenv import load_dotenv

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./model-night-467712-a8-5e7e79593d88.json"

image_annotator_client = vision_v1.ImageAnnotatorClient()
storage_client = storage.Client()

load_dotenv()

bucket_name = os.environ.get("GCP_BUCKET_NAME")
input_prefix = "Example Drawing Package"
output_prefix = "output"

if not bucket_name:
    raise RuntimeError("Missing GCP_BUCKET_NAME in .env file or environment.")

def download_pdf_from_gcs(bucket_name, blob_name, local_path):
    """Download PDF from GCS bucket to local path"""
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(local_path)
        print(f"   📥 Downloaded PDF to {local_path}")
        return True
    except Exception as e:
        print(f"   ❌ Error downloading PDF: {str(e)}")
        return False

def extract_images_from_pdf(pdf_path, output_dir):
    """Extract images from each page of the PDF and save them locally"""
    try:
        doc = fitz.open(pdf_path)
        image_paths = []
        
        # Create images subdirectory
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Convert page to image with high DPI for quality
            pix = page.get_pixmap(dpi=200)
            image_filename = f"page_{page_num + 1}.png"
            image_path = os.path.join(images_dir, image_filename)
            
            # Save the image
            pix.save(image_path)
            image_paths.append(image_path)
            print(f"   📷 Saved page {page_num + 1} as image: {image_path}")
        
        doc.close()
        return image_paths
        
    except Exception as e:
        print(f"   ❌ Error extracting images: {str(e)}")
        return []

# Loop through 8A to 12A
for i in range(1, 13):
    file_suffix = f"{i}A"
    input_file = f"{input_prefix} {file_suffix}.pdf"
    gcs_source_uri = f"gs://{bucket_name}/{input_file}"
    gcs_output_folder = f"{output_prefix}{i}"
    gcs_destination_uri = f"gs://{bucket_name}/{gcs_output_folder}/"
    
    # Create local output directory
    local_output_dir = os.path.join("ocr_results", gcs_output_folder)
    os.makedirs(local_output_dir, exist_ok=True)

    print(f"\n📝 Processing: {input_file}")
    
    # Download PDF from GCS for image extraction
    local_pdf_path = os.path.join(local_output_dir, input_file)
    pdf_downloaded = download_pdf_from_gcs(bucket_name, input_file, local_pdf_path)
    
    # Extract images from PDF if download was successful
    if pdf_downloaded:
        print(f"   🖼️ Extracting images from {input_file}...")
        image_paths = extract_images_from_pdf(local_pdf_path, local_output_dir)
        
        # Save image paths info for later use
        if image_paths:
            image_info_file = os.path.join(local_output_dir, "image_paths.txt")
            with open(image_info_file, 'w') as f:
                for img_path in image_paths:
                    f.write(f"{img_path}\n")
            print(f"   📄 Saved image paths info: image_paths.txt")
        
        # Clean up the downloaded PDF to save space
        try:
            os.remove(local_pdf_path)
            print(f"   🧹 Cleaned up temporary PDF")
        except:
            pass
    else:
        print(f"   ⚠️ Skipping image extraction due to PDF download failure")
        image_paths = []
    
    # Set up input and output config for GCP Vision OCR
    gcs_source = vision_v1.GcsSource(uri=gcs_source_uri)
    input_config = vision_v1.InputConfig(gcs_source=gcs_source, mime_type="application/pdf")

    gcs_destination = vision_v1.GcsDestination(uri=gcs_destination_uri)
    output_config = vision_v1.OutputConfig(gcs_destination=gcs_destination, batch_size=1)

    # Async request for OCR
    async_request = vision_v1.AsyncAnnotateFileRequest(
        features=[vision_v1.Feature(type_=vision_v1.Feature.Type.DOCUMENT_TEXT_DETECTION)],
        input_config=input_config,
        output_config=output_config
    )

    print(f"   🔍 Starting GCP Vision API OCR processing...")
    operation = image_annotator_client.async_batch_annotate_files(requests=[async_request])
    print("   ⏳ Waiting for OCR to complete...")
    operation.result(timeout=300)
    print(f"   ✅ OCR results saved to: {gcs_destination_uri}")

    # Download OCR results
    print("   ⬇️ Downloading OCR results...")
    blobs = storage_client.list_blobs(bucket_name, prefix=gcs_output_folder)

    downloaded_files = []
    for blob in blobs:
        if blob.name.endswith(".json"):
            filename = os.path.basename(blob.name)
            local_path = os.path.join(local_output_dir, filename)
            blob.download_to_filename(local_path)
            downloaded_files.append(local_path)
            print(f"   📄 Downloaded OCR result: {filename}")
    
    print(f"   🎉 Completed processing {input_file}")
    print(f"      - OCR files: {len(downloaded_files)}")
    print(f"      - Images: {len(image_paths)}")

print(f"\n✨ All processing complete!")
print(f"📁 Results saved in ocr_results/ directory")
print(f"📄 Each output folder contains OCR JSON files and extracted images")