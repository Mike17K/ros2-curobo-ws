import rclpy
from rclpy.node import Node

import cv2
import torch
from depth_anything_v2.dpt import DepthAnythingV2
import numpy as np 
import os
import re
import time

from custom_msgs.srv import DepthImageGeneration
from cv_bridge import CvBridge

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

class DepthAnalyzerNode(Node): # Κληρονομικότητα
    def __init__(self):
        super().__init__('node_name') # Όνομα του Node στον graph
        self.get_logger().info('Ο Node ξεκίνησε!')
        self.depth_model = DepthAnythingV2Inference()

        self.generate_depth_srv = self.create_service(DepthImageGeneration, 'generate_depth', self.handle_generate_depth)
        self.bridge = CvBridge()
   
    def handle_generate_depth(self, request, response):
        # 1. Μετατροπή ROS Image σε OpenCV
        cv_image = self.bridge.imgmsg_to_cv2(request.input_image, "bgr8")

        # 2. Inference
        depth_map = self.analyze_image(cv_image) # Αυτό επιστρέφει float32
        
        # --- ΚΡΙΣΙΜΗ ΠΡΟΣΘΗΚΗ: Μετατροπή σε uint8 για το ROS Image ---
        # Κανονικοποίηση στο 0-255
        depth_min, depth_max = depth_map.min(), depth_map.max()
        if depth_max > depth_min:
            depth_norm = (depth_map - depth_min) / (depth_max - depth_min) * 255.0
        else:
            depth_norm = depth_map * 0.0
            
        depth_uint8 = depth_norm.astype(np.uint8)
        # -----------------------------------------------------------

        # 3. Μετατροπή σε ROS Image
        response.output_image = self.bridge.cv2_to_imgmsg(depth_uint8, "mono8")
        response.success = True
        self.get_logger().info('Depth image generated successfully!')
        return response


    def analyze_image(self, img):
        start_time = time.time()
        depth = self.depth_model.infer_image(img)
        end_time = time.time()
        self.get_logger().info(f'Inference completed in {end_time - start_time:.2f} seconds')
        return depth

def main(args=None):
    rclpy.init(args=args) # Αρχικοποίηση επικοινωνίας
    node = DepthAnalyzerNode()
    rclpy.spin(node)      # Διατηρεί τον Node ζωντανό
    rclpy.shutdown()      # Καθαρή έξοδος

if __name__ == '__main__':
    main()
