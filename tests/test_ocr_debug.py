#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sparkjar_shared.tools.image_viewer_tool import ImageViewerTool

# Test with a simple image
tool = ImageViewerTool()

# Create a dummy test image file
import base64
from pathlib import Path

# Small 1x1 white PNG
test_png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==")
test_path = "/tmp/test_image.png"
with open(test_path, "wb") as f:
    f.write(test_png)

print("Testing OCR tool...")
result = tool._run(test_path)
print(f"Result: {result}")