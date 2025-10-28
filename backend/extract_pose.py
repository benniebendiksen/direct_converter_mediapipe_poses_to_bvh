# extract_pose.py
import argparse, json, cv2, mediapipe as mp

def run(input_path, output_path):
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(static_image_mode=False, model_complexity=1)
    cap = cv2.VideoCapture(input_path)
    all_frames = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)
        if results.pose_landmarks:
            frame_data = [
                {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
                for lm in results.pose_landmarks.landmark
            ]
            all_frames.append(frame_data)

    cap.release()
    with open(output_path, "w") as f:
        json.dump(all_frames, f)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", default="pose_output.json")
    args = ap.parse_args()
    run(args.input, args.output)
