import cv2
import numpy as np
import os
import easyocr
import json
from textdistance import levenshtein
from ultralytics import YOLO
from moviepy.editor import *
import numpy as np
import torch
from transformers import (
    AutoProcessor,
    AutoModelForCausalLM
)

class VideoCaptioningModel:
    def __init__(self):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        self.model = AutoModelForCausalLM.from_pretrained("microsoft/Florence-2-base", 
                                                          torch_dtype=self.torch_dtype, 
                                                          trust_remote_code=True).to(self.device)
        self.processor = AutoProcessor.from_pretrained("microsoft/Florence-2-base", 
                                                       trust_remote_code=True)

    def get_caption(self, 
                    image: np.array,
                    task_prompt: str='<MORE_DETAILED_CAPTION>'):
        height, width, _ = image.shape
        inputs = self.processor(text=task_prompt, images=image, return_tensors="pt").to(self.device, torch.float16)
        generated_ids = self.model.generate(
            input_ids=inputs["input_ids"].cuda(),
            pixel_values=inputs["pixel_values"].cuda(),
            max_new_tokens=1024,
            early_stopping=False,
            do_sample=False,
            num_beams=3,
        )
        generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        parsed_answer = self.processor.post_process_generation(
            generated_text,
            task=task_prompt,
            image_size=(width, height)
        )
        return parsed_answer[task_prompt]

class Caption():
    def __init__(self):
        self.video_captioning_model = VideoCaptioningModel()
        self.reader = easyocr.Reader(['en', 'ru'])
        self.yolo = YOLO("yolov8l.pt")
        self.yolo_names = self.yolo.names
    
    def calculate_histogram(self, frame):
        # Convert frame to HSV color space
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Calculate histogram
        hist = cv2.calcHist([hsv_frame], [0, 1], None, [50, 60], [0, 180, 0, 256])
        # Normalize the histogram
        cv2.normalize(hist, hist)
        return hist.flatten()

    def shot_transit(self, 
                     input_file,
                     threshold: int=0.7):
        cap = cv2.VideoCapture(input_file)
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = round(cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps)

        previous_hist = None
        scene_changes = [0.0]
        frame_list = []
        results = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            current_hist = self.calculate_histogram(frame)
            if previous_hist is not None:
                # Use correlation to compare histograms
                similarity = cv2.compareHist(previous_hist, current_hist, cv2.HISTCMP_CORREL)

                # Scene change threshold
                if similarity < threshold:
                    scene_changes.append(round((int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1) / fps, 2))  # Log time of new scene start
                    frame_list.append(frame) # Add first scene frame to list
            else:
                frame_list.append(frame)

            # Update previous histogram
            previous_hist = current_hist
        
        # get captions of each scene
        for frame, start_time in zip(frame_list, scene_changes):
            caption = self.video_captioning_model.get_caption(frame)
            results.append({'scene_start': start_time, 'caption': caption})
        return json.dumps(results, ensure_ascii=False)
