"""Just a snippet for converting image arrays to an image"""

import cv2
from PIL import Image
import numpy as np

arr = np.load("/work/KristianGadeKjelmann#9065/MP_ACID/Pipelines/Screengetter/Data/Framearrays/C4_11/474.0_474.0.npy")

#mean_frame = np.mean(screenshots, axis = 0).astype(np.uint8)
#frame_rgb = cv2.cvtColor(mean_frame, cv2.COLOR_BGR2RGB)

## OpenCV uses BGR; PIL expects RGB.
frame_rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
screenshot = Image.fromarray(frame_rgb)