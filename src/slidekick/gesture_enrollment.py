import os
import json
import base64
import time
from datetime import datetime, timezone

class EnrollmentSession:
    """
    Manages the guided gesture data collection session to satisfy the 
    Sprint 5 R03 <-> R04 Data Training Contract.
    """
    # The 8 specific stages required by Diego's training pipeline
    STAGES = [
        "neutral", 
        "slight left tilt", 
        "slight right tilt", 
        "closer", 
        "farther", 
        "reposition", 
        "reform", 
        "final confirmation"
    ]
    
    def __init__(self, profile_id, enrollment_id, gesture_name):
        self.profile_id = profile_id
        self.enrollment_id = enrollment_id
        self.gesture_name = gesture_name
        self.status = "collecting"
        self.samples = []
        self.target_per_stage = 8
        self.current_stage_index = 0

    def add_sample(self, base64_image, guided_stage_id, capture_group_id, output_dir):
        """
        Receives a webcam frame, decodes it, saves as a JPEG, and logs it.
        """
        if self.status != "collecting":
            return {"error": "Session is not in collecting state."}
            
        if guided_stage_id not in self.STAGES:
            return {"error": f"Invalid stage: {guided_stage_id}"}
            
        # Ensure the image output directory exists
        gesture_dir = os.path.join(output_dir, "images", self.gesture_name)
        os.makedirs(gesture_dir, exist_ok=True)
        
        # Generate a unique sample ID and file path
        timestamp = int(time.time() * 1000)
        sample_id = f"{self.gesture_name}_{capture_group_id}_{timestamp}"
        filepath = os.path.join(gesture_dir, f"{sample_id}.jpg")
        
        # Decode the base64 image from the frontend and save as JPEG
        try:
            if "," in base64_image:
                base64_image = base64_image.split(",")[1]
            image_bytes = base64.b64decode(base64_image)
            with open(filepath, "wb") as img_file:
                img_file.write(image_bytes)
        except Exception as e:
            return {"error": "Failed to save image", "details": str(e)}
            
        # Log the required capture metadata for the manifest
        sample_record = {
            "sample_id": sample_id,
            "gesture_id": self.gesture_name,
            "image_ref": filepath,
            "capture_group_id": capture_group_id,
            "guided_stage_id": guided_stage_id,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "mirrored": True
        }
        self.samples.append(sample_record)
        
        # Check if we hit the ~8 image target for the current stage
        stage_samples = [s for s in self.samples if s["guided_stage_id"] == guided_stage_id]
        if len(stage_samples) >= self.target_per_stage:
            self.current_stage_index += 1
            if self.current_stage_index >= len(self.STAGES):
                self.status = "validating"

        return {
            "status": "success", 
            "sample_id": sample_id,
            "current_stage": guided_stage_id,
            "stage_count": len(stage_samples)
        }
        
    def complete_session(self, storage_dir):
        """
        Finalizes the session and exports the versioned dataset manifest JSON.
        """
        if self.status not in ["collecting", "validating"]:
            return {"error": "Cannot complete session in current state."}
            
        self.status = "completed"
        os.makedirs(storage_dir, exist_ok=True)
        
        # Build the exact manifest structure Diego's pipeline expects
        manifest = {
            "schema_version": "1.0",
            "dataset_version": "1.0",
            "profile_id": self.profile_id,
            "enrollment_id": self.enrollment_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "class_manifest": {
                "gesture_id": self.gesture_name,
                "class_label": self.gesture_name,
                "display_name": self.gesture_name.replace("_", " ").title(),
                "sample_ids": [s["sample_id"] for s in self.samples]
            },
            "samples": self.samples
        }
        
        manifest_path = os.path.join(storage_dir, f"{self.enrollment_id}_manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=4)
            
        return {
            "status": "success",
            "manifest_file": manifest_path,
            "total_images_saved": len(self.samples)
        }

    def cancel_session(self):
        self.status = "cancelled"
        self.samples.clear()
        return {"status": "cancelled"}