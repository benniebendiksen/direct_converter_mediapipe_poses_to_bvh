# extract_pose_webcam.py
import argparse
import json
import time

import cv2
import mediapipe as mp


def run(device_index: int, output_path: str, duration: float = None, max_frames: int = None):
    """
    Capture pose landmarks from a webcam and save them to JSON.

    - device_index: which camera (0 is default).
    - output_path: where to save JSON.
    - duration: optional, stop after N seconds.
    - max_frames: optional, stop after N frames.
    You can always stop manually by pressing 'q' in the preview window.
    """

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open webcam with index {device_index}")

    all_frames = []
    start_time = time.time()

    print("✅ Webcam capture started. Press 'q' to stop.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Failed to read frame from webcam, stopping.")
            break

        # Show a small preview so you can see what you're doing
        cv2.imshow("Webcam Pose Capture - press 'q' to stop", frame)

        # Mediapipe expects RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            frame_data = [
                {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
                for lm in results.pose_landmarks.landmark
            ]
            all_frames.append(frame_data)

        # --- stopping conditions ---

        # 1) user presses 'q'
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("⏹ Stopped by user (q pressed).")
            break

        # 2) max duration
        if duration is not None and (time.time() - start_time) >= duration:
            print(f"⏹ Reached duration limit of {duration} seconds.")
            break

        # 3) max frames
        if max_frames is not None and len(all_frames) >= max_frames:
            print(f"⏹ Reached max_frames limit of {max_frames}.")
            break

    cap.release()
    cv2.destroyAllWindows()

    # Save JSON in the SAME format as your video extractor
    with open(output_path, "w") as f:
        json.dump(all_frames, f)

    print(f"💾 Saved {len(all_frames)} frames to {output_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=int, default=0, help="Webcam index (default 0)")
    ap.add_argument("--output", default="webcam_pose_output.json", help="Output JSON path")
    ap.add_argument("--duration", type=float, default=None,
                    help="Optional: record for N seconds then stop")
    ap.add_argument("--max-frames", type=int, default=None,
                    help="Optional: record at most N frames")
    args = ap.parse_args()

    run(
        device_index=args.device,
        output_path=args.output,
        duration=args.duration,
        max_frames=args.max_frames,
    )
