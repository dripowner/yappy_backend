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
    AutoImageProcessor,
    AutoTokenizer,
    VisionEncoderDecoderModel
)

class VideoCaptioningModel:
    def __init__(self):
        self.image_processor = AutoImageProcessor.from_pretrained(
            "MCG-NJU/videomae-large",
            dtype=torch.float16
        )
        self.tokenizer = AutoTokenizer.from_pretrained("gpt2")
        self.model = VisionEncoderDecoderModel.from_pretrained(
            "Neleac/timesformer-gpt2-video-captioning"
        ).to("cuda")

    def get_caption(self, cap):
        # Извлекаем данные из объекта cv2.VideoCapture
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        seg_len = frame_count
        clip_len = self.model.config.encoder.num_frames
        indices = set(np.linspace(0, seg_len, num=clip_len, endpoint=False).astype(np.int64))
        frames = []
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        for i in range(frame_count):
            ret, frame = cap.read()
            if not ret:
                break
            if i in indices:
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        gen_kwargs = {
            "min_length": 16,
            "max_length": 128,
            "num_beams": 8,
        }
        pixel_values = self.image_processor(frames, return_tensors="pt").pixel_values.to("cuda")
        tokens = self.model.generate(pixel_values, **gen_kwargs)
        caption = self.tokenizer.batch_decode(tokens, skip_special_tokens=True)[0]
        return caption, tokens

class Caption():
    def __init__(self):
        self.video_captioning_model = VideoCaptioningModel()
        self.reader = easyocr.Reader(['en', 'ru'])
        self.yolo = YOLO("yolov8l.pt")
        self.yolo_names = self.yolo.names

    def shot_transit(self, input_file):
        cap = cv2.VideoCapture(input_file)
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = round(cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps)
        if duration < 60:
            time_intervals = 5
        elif duration >= 60:
            time_intervals = 10
        results = []
        timecode = 0.0
        ocr_text = ''

        while timecode <= duration:
            start_time = timecode
            end_time = timecode + time_intervals
            if end_time > duration:
                end_time = duration

            # Выполняем OCR на первой и предпоследней секунде
            obj = []
            for i in [1, 3, 5]:
                frame_time = start_time + i
                if frame_time > duration:
                    frame_time = duration
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_time * fps)
                ret, frame = cap.read()

                if not ret:
                    break

                try:
                    cv2.imwrite("temp_img.jpg", frame)
                    detection = self.yolo.predict("temp_img.jpg")

                    for r in detection:
                        for c in r.boxes.cls:
                            if len(r.boxes.conf) > int(c):
                                confidence = r.boxes.conf[int(c)]
                                if self.yolo_names[int(c)] not in obj and confidence >= 0.9:
                                    obj.append(self.yolo_names[int(c)])
                except cv2.error as e:
                    print(f"Error saving frame to file: {e}")

                result = ' '.join([r[1] for r in self.reader.readtext(frame)])
                distance = levenshtein.normalized_similarity(ocr_text, result)
                if distance < 0.8:
                    ocr_text = result
                os.remove("temp_img.jpg")

            caption = self.video_captioning_model.get_caption(cap)
            results.append({'interval': end_time, 'caption': caption[0], 'ocr': ocr_text, 'obj': obj})
            timecode += time_intervals

        return json.dumps(results, ensure_ascii=False)
