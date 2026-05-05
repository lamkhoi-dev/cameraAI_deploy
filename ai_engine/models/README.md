# This directory contains YOLO model weight files
# Model files should be placed here before deployment:

# - yolo11s-pose.pt (or .engine after TensorRT export)
# - yolo11s.pt (or .engine after TensorRT export) 
# - yolo11n-fire.pt (or .engine - custom trained fire detection)
# - yolo11n-plate.pt (or .engine - custom trained license plate detection)

# For Tesla P4 GPU optimization, export models to TensorRT FP16:
# python -c "from ultralytics import YOLO; YOLO('yolo11s-pose.pt').export(format='engine', device=0, half=True)"
