# Direct pose landmarks to BVH File Conversion

Reads-in a json of MediaPipe pose landmarks and converts them to a BVH file. Having a pose_output.json file in the docs file plus pressing Play on the hosted webpage is all that is required.

## Usage
    
```bash

git clone https://github.com/benniebendiksen/direct_converter_mediapipe_pose_to_bvh.git
cd direct_converter_mediapipe_pose_to_bvh
```
## backend (Terminal 1)

```bash
cd backend
python server.py
```
## front end (Terminal 2)
```bash
cd direct_converter_mediapipe_pose_to_bvh/docs
npx http-server . -p 8080
```
