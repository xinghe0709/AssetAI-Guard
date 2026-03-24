#progressTracker.py
import threading
from flask import Blueprint, jsonify

class ProgressStatus:
    def __init__(self):
        self.percent = 0
        self.status_text = ""
        self.lock = threading.Lock()

        # Stage-based progress tracking for batch processing
        self.total_files = 0
        self.is_batch_mode = False
        self.stage_completion = {}  # stage_name: completed_count
        self.current_files_in_stage = {}  # stage_name: set of files currently in this stage
        
        # Define processing stages with their progress weights
        self.stages = [
            (5, "initializing", "Initializing batch processing..."),
            (15, "file_preparation", "Preparing files for processing..."),
            (25, "uploading_to_gcs", "Uploading files to cloud storage..."),
            (45, "ocr_processing", "Extracting text from documents..."),
            (70, "ai_analysis", "Analyzing content with AI..."),
            (90, "building_artifacts", "Building reports and artifacts..."),
            (100, "completed", "All files processed successfully!")
        ]

    def reset(self):
        with self.lock:
            self.percent = 0
            self.status_text = ""
            self.total_files = 0
            self.is_batch_mode = False
            self.stage_completion = {}
            self.current_files_in_stage = {}

    def start_batch(self, total_files):
        """Start batch processing with given number of files"""
        with self.lock:
            self.is_batch_mode = True
            self.total_files = total_files
            self.stage_completion = {stage[1]: 0 for stage in self.stages}
            self.current_files_in_stage = {stage[1]: set() for stage in self.stages}
            self.percent = 0
            self.status_text = f"Starting to process {total_files} file{'s' if total_files > 1 else ''}..."

    def file_enter_stage(self, filename, stage_name):
        """Mark that a file has entered a specific processing stage"""
        with self.lock:
            if not self.is_batch_mode or stage_name not in self.current_files_in_stage:
                return
            
            self.current_files_in_stage[stage_name].add(filename)
            self._update_progress_from_stages()

    def file_complete_stage(self, filename, stage_name):
        """Mark that a file has completed a specific processing stage"""
        with self.lock:
            if not self.is_batch_mode or stage_name not in self.stage_completion:
                return

            # Remove from current stage and add to completed
            if filename in self.current_files_in_stage.get(stage_name, set()):
                self.current_files_in_stage[stage_name].remove(filename)
            
            self.stage_completion[stage_name] += 1
            self._update_progress_from_stages()

    def _update_progress_from_stages(self):
        """Internal method to calculate progress based on stage completion"""
        if not self.is_batch_mode or self.total_files == 0:
            return

        # Find the most advanced stage where all files have completed
        completed_stage_percent = 0
        completed_stage_text = ""
        
        for percent, stage_name, stage_text in self.stages:
            completed_count = self.stage_completion.get(stage_name, 0)
            
            if completed_count >= self.total_files:
                # All files completed this stage
                completed_stage_percent = percent
                completed_stage_text = stage_text
            else:
                # This stage is not fully completed, check if any files are in progress
                in_progress_count = len(self.current_files_in_stage.get(stage_name, set()))
                
                if in_progress_count > 0:
                    # Some files are in this stage, show partial progress
                    progress_in_stage = (completed_count + in_progress_count * 0.5) / self.total_files
                    partial_percent = completed_stage_percent + (percent - completed_stage_percent) * progress_in_stage
                    
                    if in_progress_count == self.total_files:
                        # All files are in this stage
                        self.status_text = stage_text
                    else:
                        # Mixed progress
                        self.status_text = f"{stage_text} ({completed_count + in_progress_count}/{self.total_files})"
                    
                    self.percent = min(99, partial_percent)  # Cap at 99% until truly complete
                    return
                
                # No files in progress for this stage, stick with previous completed stage
                break
        
        # Update to the last fully completed stage
        self.percent = completed_stage_percent
        if completed_stage_percent >= 100:
            # Only show final success message if all files have completed ALL stages including the final "completed" stage
            final_completed_count = self.stage_completion.get("completed", 0)
            if final_completed_count >= self.total_files:
                self.status_text = f"All {self.total_files} file{'s' if self.total_files > 1 else ''} processed successfully!"
            else:
                # Still building artifacts or finalizing
                self.status_text = completed_stage_text
                self.percent = min(99, completed_stage_percent)  # Cap at 99% until truly done
        else:
            self.status_text = completed_stage_text

    def update_single_file_progress(self, percent, status_text):
        """Update progress for single file processing (non-batch)"""
        with self.lock:
            if not self.is_batch_mode:
                self.percent = percent
                self.status_text = status_text

    def update(self, percent, status_text):
        """Direct update (for backward compatibility or manual override)"""
        with self.lock:
            self.percent = percent
            self.status_text = status_text

    def get(self):
        with self.lock:
            return {
                "percent": self.percent,
                "status_text": self.status_text,
                "is_batch_mode": self.is_batch_mode,
                "total_files": self.total_files
            }

progress_status = ProgressStatus()

bp = Blueprint('process_status', __name__)

@bp.route('/api/process-status', methods=['GET'])
def get_process_status():
    return jsonify(progress_status.get())

@bp.route('/api/process-status-reset', methods=['POST'])
def reset_process_status():
    progress_status.reset()
    return jsonify({'success': True, 'message': 'Progress status reset.'})