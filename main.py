from vision import detect_pips
import sys

image_path = sys.argv[1]
coordinates = detect_pips(image_path)
for k, v in coordinates.items():
    print(k, '     ', v)
