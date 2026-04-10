import cv2
import torch
from depth_anything_v2.dpt import DepthAnythingV2
import numpy as np 
import os
import re
import time

class DepthAnythingV2Inference:
    def __init__(self, model_path='assets/checkpoints/depth_anything_v2_vits.pth'):
        # 1. Όρισε τη συσκευή (CUDA αν υπάρχει, αλλιώς CPU)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f'Using device: {self.device}')

        # 2. Φόρτωσε το μοντέλο και βάλε το σε evaluation mode
        self.model = DepthAnythingV2(encoder='vits', features=64, out_channels=[48, 96, 192, 384])
        self.model.load_state_dict(torch.load(model_path, map_location='cpu'))
        self.model.to(self.device).eval() 

    def infer_image(self, img):
        with torch.no_grad():
            depth = self.model.infer_image(img)
        return depth
    
    def save_depth(self, depth, output_path):
        # 1. Normalize στο εύρος 0-255
        depth_norm = (depth - depth.min()) / (depth.max() - depth.min()) * 255.0
        depth_norm = depth_norm.astype(np.uint8)

        # 2. Προαιρετικά: Εφάρμοσε ένα ColorMap για να φαίνεται "ωραίο" (π.χ. Magma ή Infero)
        depth_color = cv2.applyColorMap(depth_norm, cv2.COLORMAP_INFERNO)

        # Σώσε την εικόνα (την normalized ή την έγχρωμη)
        cv2.imwrite(output_path, depth_color)

def main():
    depth_model = DepthAnythingV2Inference()

    # Performance test

    directory = 'assets/examples/'
    image_rgx = r'.*\.(jpg|jpeg|png|bmp|tiff)$'

    # Ταξινόμηση για να είναι σε σωστή σειρά
    files = sorted([f for f in os.listdir(directory) if re.match(image_rgx, f)])

    # Φόρτωση των εικόνων
    data = {f.split('.')[0]: cv2.imread(os.path.join(directory, f)) for f in files}

    # Έλεγχος αν φορτώθηκαν σωστά (προαιρετικό αλλά σωτήριο)

    startTime = time.time()
    depths = {}
    for label in data:
        print(f'Processing {label}...')
        startTimeTmp = time.time()
        depth = depth_model.infer_image(data[label])
        depths[label] = depth
        print(f'Inference for {label} completed in {time.time() - startTimeTmp:.2f} seconds.')

    for label, depth in depths.items():
        depth_model.save_depth(depth, os.path.join('assets/outputs/', f'depth_{os.path.basename(label)}.png'))

    print('Inference completed! Depth maps saved in assets/outputs/')
    print(f'Total processing time: {time.time() - startTime:.2f} seconds.')


if __name__ == "__main__":
    main()