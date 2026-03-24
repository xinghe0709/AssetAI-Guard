// Simple Progress Bar JavaScript functionality

class ProgressTracker {
    constructor() {
      this.container = document.getElementById("progressBarContainer");
      this.progressText = document.getElementById("progressText");
      this.progressPercent = document.getElementById("progressPercent");
      this.progressFill = document.getElementById("progressFill");
  
      this.isTracking = false;
      this.trackingInterval = null;
    }
  
    show() {
      if (this.container) {
        this.container.style.display = "block";
      }
    }
  
    hide() {
      if (this.container) {
        this.container.style.display = "none";
      }
    }
  
    updateProgress(percent, statusText) {
      const roundedPercent = Math.round(percent);
  
      if (this.progressPercent) {
        this.progressPercent.textContent = `${roundedPercent}%`;
      }
      if (this.progressText) {
        this.progressText.textContent = statusText || "";
      }
      if (this.progressFill) {
        const clampedPercent = Math.min(100, Math.max(0, percent));
        this.progressFill.style.width = `${clampedPercent}%`;
  
        // Mark as complete if 100%
        if (clampedPercent >= 100) {
          this.progressFill.setAttribute("data-complete", "true");
        } else {
          this.progressFill.removeAttribute("data-complete");
        }
      }
    }
  
    startTracking() {
      if (this.isTracking) return;
  
      this.isTracking = true;
      this.show();
      this.updateProgress(0, "Initializing...");
  
      // Poll progress status every 500ms
      this.trackingInterval = setInterval(() => {
        this.fetchProgressStatus();
      }, 500);
    }
  
    stopTracking(forceHide = false) {
      this.isTracking = false;
  
      if (this.trackingInterval) {
        clearInterval(this.trackingInterval);
        this.trackingInterval = null;
      }
  
      if (forceHide) {
        setTimeout(() => {
          this.hide();
        }, 3000);
      }
    }
  
    async fetchProgressStatus() {
      try {
        const response = await fetch("/api/process-status");
        if (response.ok) {
          const data = await response.json();
  
          // Update progress directly from server
          this.updateProgress(
            data.percent || 0,
            data.status_text || "Processing..."
          );
  
          // Stop tracking if completed - be more specific about completion condition
          if (
            data.percent >= 100 &&
            data.status_text.includes("All") &&
            data.status_text.includes("processed successfully!")
          ) {
            // Keep showing for 2 seconds after completion
            setTimeout(() => {
              this.stopTracking(true);
            }, 2000);
          }
        }
      } catch (error) {
        console.error("Error fetching progress status:", error);
        // If we can't fetch status, assume processing might be done
        // Don't stop tracking immediately to avoid flickering
      }
    }
  
    async resetProgressStatus() {
      try {
        await fetch("/api/process-status-reset", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        });
      } catch (error) {
        console.error("Error resetting progress status:", error);
      }
    }
  }
  
  // Global progress tracker instance
  const progressTracker = new ProgressTracker();
  
  // Export for use in other scripts
  window.progressTracker = progressTracker;
  