import cv2
import numpy as np
import os
import glob
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

try:
    import mtcnn
    MTCNN_AVAILABLE = True
except ImportError:
    MTCNN_AVAILABLE = False

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

COCO_CLASSES = {
    0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck',
    8: 'boat', 9: 'traffic light', 10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench',
    14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 20: 'elephant', 21: 'bear',
    22: 'zebra', 23: 'giraffe', 24: 'backpack', 25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase',
    29: 'frisbee', 30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite', 34: 'baseball bat',
    35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket', 39: 'bottle',
    40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon', 45: 'bowl', 46: 'banana',
    47: 'apple', 48: 'sandwich', 49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza',
    54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant', 59: 'bed', 60: 'dining table',
    61: 'toilet', 62: 'tv', 63: 'laptop', 64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone',
    68: 'microwave', 69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book', 74: 'clock',
    75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush'
}

class ObjectTracker:
    def __init__(self):
        self.object_templates = {}
        self.object_centers_history = defaultdict(list)
        self.object_features = {}
        self.tracking_threshold = 0.3
        self.position_weight = 0.4
    
    def add_object_template(self, obj_id, obj_img):
        self.object_templates[obj_id] = cv2.cvtColor(obj_img, cv2.COLOR_BGR2GRAY)
        self.object_features[obj_id] = self._extract_features(obj_img)
    
    def _extract_features(self, obj_img):
        gray = cv2.cvtColor(obj_img, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (32, 32))
        hist = cv2.calcHist([resized], [0], None, [16], [0, 256])
        
        hsv = cv2.cvtColor(obj_img, cv2.COLOR_BGR2HSV)
        hsv_resized = cv2.resize(hsv, (32, 32))
        h_hist = cv2.calcHist([hsv_resized], [0], None, [8], [0, 180])
        
        return np.concatenate([hist.flatten(), h_hist.flatten()])
    
    def find_target_object(self, detections, frame, target_object_id, object_type):
        if target_object_id is None or target_object_id not in self.object_templates:
            return self._find_largest_person(detections) if detections else None
        
        template_features = self.object_features.get(target_object_id)
        best_match = None
        best_score = 0
        
        last_center = self._get_last_center(target_object_id)
        
        for detection in detections:
            x, y, w, h = detection['bbox']
            obj_region = frame[y:y+h, x:x+w]
            
            if obj_region.size == 0:
                continue
            
            obj_features = self._extract_features(obj_region)
            feature_score = np.corrcoef(template_features, obj_features)[0, 1]
            if np.isnan(feature_score):
                feature_score = 0
            
            position_score = 1.0
            if last_center:
                curr_center = (x + w//2, y + h//2)
                distance = np.sqrt((curr_center[0] - last_center[0])**2 + (curr_center[1] - last_center[1])**2)
                max_distance = max(frame.shape[0], frame.shape[1])
                position_score = max(0, 1 - (distance / max_distance))
            
            combined_score = (1 - self.position_weight) * feature_score + self.position_weight * position_score
            
            if combined_score > best_score and combined_score > self.tracking_threshold:
                best_score = combined_score
                best_match = detection
        
        if best_match:
            x, y, w, h = best_match['bbox']
            self._update_center(target_object_id, (x + w//2, y + h//2))
        
        return best_match or self._find_largest_person(detections)
    
    def _find_largest_person(self, detections):
        people = [d for d in detections if d['class_name'] == 'person']
        if not people:
            return detections[0] if detections else None
        return max(people, key=lambda d: d['bbox'][2] * d['bbox'][3])
    
    def _get_last_center(self, obj_id):
        if obj_id in self.object_centers_history and self.object_centers_history[obj_id]:
            return self.object_centers_history[obj_id][-1]
        return None
    
    def _update_center(self, obj_id, center):
        self.object_centers_history[obj_id].append(center)
        if len(self.object_centers_history[obj_id]) > 10:
            self.object_centers_history[obj_id].pop(0)

class ObjectProcessor:
    def __init__(self, input_video_path, detection_type="faces", target_classes=None, verbose=False):
        self.input_video_path = input_video_path
        self.detection_type = detection_type.lower()
        self.target_classes = target_classes or []
        self.verbose = verbose
        
        if self.detection_type == "faces":
            if MEDIAPIPE_AVAILABLE:
                self.mp_face = mp.solutions.face_detection
                self.face_detector = self.mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.7)
            elif MTCNN_AVAILABLE:
                self.mtcnn_detector = mtcnn.MTCNN(min_face_size=20, scale_factor=0.709, steps_threshold=[0.6, 0.7, 0.7])
            else:
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        else:
            if YOLO_AVAILABLE:
                self.yolo_model = YOLO('yolov8n.pt')
                self.yolo_model.fuse()
                if hasattr(self.yolo_model, 'warmup'):
                    self.yolo_model.warmup(imgsz=(1, 3, 320, 320))
            else:
                raise ImportError("ultralytics package is required for object detection. Install with: pip install ultralytics")
        
        self.cap = cv2.VideoCapture(input_video_path)
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        self.enable_blur = False
        self.enable_zoom = False
        self.blur_strength = 51
        self.zoom_factor = 2.0
        self.target_object_id = None
        
        self.prev_center_x = self.width // 2
        self.prev_center_y = self.height // 2
        self.current_zoom = 1.0
        self.zoom_momentum = 0.0
        
        self.object_tracker = ObjectTracker()
        
        self.detection_scale = 0.75
        self.frame_skip = 3
        self.batch_size = 8
        
        if self.verbose:
            print(f"Loaded video: {input_video_path}")
            print(f"Detection type: {self.detection_type}")
            print(f"Resolution: {self.width}x{self.height}, FPS: {self.fps}, Frames: {self.total_frames}")
            if self.target_classes:
                print(f"Target classes: {self.target_classes}")
            print(f"Processing with {self.frame_skip}x frame skip and {self.detection_scale}x detection scale")
    
    def detect_objects_in_frame(self, frame, use_small_scale=True):
        if use_small_scale:
            small_frame = cv2.resize(frame, None, fx=self.detection_scale, fy=self.detection_scale)
            if self.detection_type == "faces":
                detections = self._detect_faces(small_frame)
            else:
                detections = self._detect_objects_yolo(small_frame)
            
            for detection in detections:
                x, y, w, h = detection['bbox']
                detection['bbox'] = (int(x/self.detection_scale), int(y/self.detection_scale), 
                                   int(w/self.detection_scale), int(h/self.detection_scale))
            return detections
        else:
            if self.detection_type == "faces":
                return self._detect_faces(frame)
            else:
                return self._detect_objects_yolo(frame)
    
    def _detect_faces(self, frame):
        if MEDIAPIPE_AVAILABLE:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detector.process(rgb_frame)
            
            detections = []
            if results.detections:
                for i, detection in enumerate(results.detections):
                    bbox = detection.location_data.relative_bounding_box
                    h, w, _ = frame.shape
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    x = max(0, x)
                    y = max(0, y)
                    width = min(width, w - x)
                    height = min(height, h - y)
                    
                    detections.append({
                        'id': i,
                        'bbox': (x, y, width, height),
                        'class_name': 'face',
                        'confidence': detection.score[0]
                    })
            return detections
        elif MTCNN_AVAILABLE:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.mtcnn_detector.detect_faces(rgb_frame)
            
            detections = []
            for i, face in enumerate(result):
                if face['confidence'] > 0.85:
                    x, y, w, h = face['box']
                    detections.append({
                        'id': i,
                        'bbox': (x, y, w, h),
                        'class_name': 'face',
                        'confidence': face['confidence']
                    })
            return detections
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.05, 4, minSize=(40, 40), maxSize=(300, 300))
            
            detections = []
            for i, (x, y, w, h) in enumerate(faces):
                detections.append({
                    'id': i,
                    'bbox': (x, y, w, h),
                    'class_name': 'face',
                    'confidence': 1.0
                })
            
            return detections
    
    def _detect_objects_yolo(self, frame):
        results = self.yolo_model(frame, verbose=False, imgsz=320, conf=0.25, iou=0.45, max_det=20)
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for i, box in enumerate(boxes):
                    confidence = float(box.conf[0].cpu().numpy())
                    if confidence < 0.4:
                        continue
                        
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x, y, w, h = int(x1), int(y1), int(x2-x1), int(y2-y1)
                    
                    if w < 10 or h < 10:
                        continue
                    
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = COCO_CLASSES.get(class_id, f"class_{class_id}")
                    
                    if self.target_classes and class_name not in self.target_classes:
                        continue
                    
                    detections.append({
                        'id': i,
                        'bbox': (x, y, w, h),
                        'class_name': class_name,
                        'confidence': confidence
                    })
        
        return detections
    
    def extract_objects(self, output_folder="detected_objects", sample_frames=15):
        if os.path.exists(output_folder):
            import shutil
            shutil.rmtree(output_folder)
        os.makedirs(output_folder, exist_ok=True)
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        unique_objects = {}
        object_id_counter = 0
        frame_interval = max(1, self.total_frames // sample_frames)
        
        if self.verbose:
            print(f"Extracting {self.detection_type} from video (sampling every {frame_interval} frames)...")
        
        frame_count = 0
        frames_to_process = []
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                frames_to_process.append((frame_count, frame.copy()))
            
            frame_count += 1
        
        def process_frame_batch(frame_data):
            frame_count, frame = frame_data
            detections = self.detect_objects_in_frame(frame, use_small_scale=True)
            return [(frame_count, detection, frame) for detection in detections]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            batch_results = list(executor.map(process_frame_batch, frames_to_process))
        
        for batch in batch_results:
            for frame_count, detection, frame in batch:
                x, y, w, h = detection['bbox']
                if w < 20 or h < 20:
                    continue
                    
                obj_img = frame[y:y+h, x:x+w]
                class_name = detection['class_name']
                
                is_new_object = True
                for obj_id, stored_obj in unique_objects.items():
                    if self._objects_similar_fast(obj_img, stored_obj['image']):
                        is_new_object = False
                        break
                
                if is_new_object:
                    obj_filename = f"{class_name}_{object_id_counter}.jpg"
                    obj_path = os.path.join(output_folder, obj_filename)
                    cv2.imwrite(obj_path, obj_img)
                    unique_objects[object_id_counter] = {
                        'image': obj_img,
                        'class_name': class_name,
                        'filename': obj_filename
                    }
                    object_id_counter += 1
                    
                    if self.verbose:
                        print(f"Found new {class_name}: {obj_filename}")
        
        if self.verbose:
            print(f"Extracted {len(unique_objects)} unique objects to '{output_folder}' folder")
        
        return list(unique_objects.keys())
    
    def get_detected_objects(self, output_folder="detected_objects"):
        if not os.path.exists(output_folder):
            return []
        
        object_files = glob.glob(os.path.join(output_folder, "*.jpg"))
        return sorted(object_files)
    
    def find_similar_object_from_image(self, input_image_path, output_folder="detected_objects", threshold=0.6, method="histogram"):
        if isinstance(input_image_path, str):
            query_img = cv2.imread(input_image_path)
        else:
            query_img = input_image_path
        
        if query_img is None:
            return None
        
        if method == "embedding" and FACE_RECOGNITION_AVAILABLE and self.detection_type == "faces":
            return self._find_similar_face_embedding(query_img, output_folder, threshold)
        elif method == "cosine":
            return self._find_similar_object_cosine(query_img, output_folder, threshold)
        else:
            return self._find_similar_object_histogram(query_img, output_folder, threshold)
    
    def _find_similar_face_embedding(self, query_img, output_folder, threshold):
        query_rgb = cv2.cvtColor(query_img, cv2.COLOR_BGR2RGB)
        query_encodings = face_recognition.face_encodings(query_rgb)
        
        if not query_encodings:
            if self.verbose:
                print("No face found in query image")
            return None
        
        query_encoding = query_encodings[0]
        
        best_match = None
        best_distance = float('inf')
        
        detected_objects = self.get_detected_objects(output_folder)
        
        for obj_path in detected_objects:
            obj_img = cv2.imread(obj_path)
            if obj_img is None:
                continue
            
            obj_rgb = cv2.cvtColor(obj_img, cv2.COLOR_BGR2RGB)
            obj_encodings = face_recognition.face_encodings(obj_rgb)
            
            if not obj_encodings:
                continue
            
            obj_encoding = obj_encodings[0]
            distance = face_recognition.face_distance([query_encoding], obj_encoding)[0]
            
            if distance < best_distance and distance < threshold:
                best_distance = distance
                best_match = os.path.basename(obj_path).split('.')[0]
        
        if self.verbose and best_match:
            print(f"Best match: {best_match} with distance: {best_distance:.3f}")
        
        return best_match
    
    def _find_similar_object_histogram(self, query_img, output_folder, threshold):
        query_gray = cv2.cvtColor(query_img, cv2.COLOR_BGR2GRAY)
        query_hist = cv2.calcHist([query_gray], [0], None, [256], [0, 256])
        
        best_match = None
        best_score = 0
        
        detected_objects = self.get_detected_objects(output_folder)
        
        for obj_path in detected_objects:
            obj_img = cv2.imread(obj_path)
            if obj_img is None:
                continue
            
            obj_gray = cv2.cvtColor(obj_img, cv2.COLOR_BGR2GRAY)
            obj_resized = cv2.resize(obj_gray, (query_gray.shape[1], query_gray.shape[0]))
            obj_hist = cv2.calcHist([obj_resized], [0], None, [256], [0, 256])
            
            score = cv2.compareHist(query_hist, obj_hist, cv2.HISTCMP_CORREL)
            
            if score > best_score and score > threshold:
                best_score = score
                best_match = os.path.basename(obj_path).split('.')[0]
        
        return best_match
    
    def _find_similar_object_cosine(self, query_img, output_folder, threshold):
        query_features = self._extract_object_features(query_img)
        if query_features is None:
            return None
        
        best_match = None
        best_score = 0
        
        detected_objects = self.get_detected_objects(output_folder)
        
        for obj_path in detected_objects:
            obj_img = cv2.imread(obj_path)
            if obj_img is None:
                continue
            
            obj_features = self._extract_object_features(obj_img)
            if obj_features is None:
                continue
            
            if SKLEARN_AVAILABLE:
                score = cosine_similarity([query_features], [obj_features])[0][0]
            else:
                score = self._cosine_similarity_manual(query_features, obj_features)
            
            if score > best_score and score > threshold:
                best_score = score
                best_match = os.path.basename(obj_path).split('.')[0]
        
        return best_match
    
    def _extract_object_features(self, obj_img):
        gray = cv2.cvtColor(obj_img, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (64, 64))
        
        lbp_features = self._compute_lbp(resized)
        hog_features = self._compute_hog(resized)
        color_features = self._compute_color_features(obj_img)
        
        features = np.concatenate([lbp_features, hog_features, color_features])
        return features / np.linalg.norm(features)
    
    def _compute_lbp(self, gray_img):
        height, width = gray_img.shape
        lbp_img = np.zeros_like(gray_img)
        
        for i in range(1, height-1):
            for j in range(1, width-1):
                center = gray_img[i, j]
                code = 0
                code |= (gray_img[i-1, j-1] >= center) << 7
                code |= (gray_img[i-1, j] >= center) << 6
                code |= (gray_img[i-1, j+1] >= center) << 5
                code |= (gray_img[i, j+1] >= center) << 4
                code |= (gray_img[i+1, j+1] >= center) << 3
                code |= (gray_img[i+1, j] >= center) << 2
                code |= (gray_img[i+1, j-1] >= center) << 1
                code |= (gray_img[i, j-1] >= center) << 0
                lbp_img[i, j] = code
        
        hist, _ = np.histogram(lbp_img.ravel(), bins=256, range=(0, 256))
        return hist.astype(np.float32)
    
    def _compute_hog(self, gray_img):
        gx = cv2.Sobel(gray_img, cv2.CV_32F, 1, 0, ksize=1)
        gy = cv2.Sobel(gray_img, cv2.CV_32F, 0, 1, ksize=1)
        
        magnitude = np.sqrt(gx**2 + gy**2)
        angle = np.arctan2(gy, gx) * 180 / np.pi
        angle[angle < 0] += 180
        
        hist, _ = np.histogram(angle.ravel(), bins=9, range=(0, 180), weights=magnitude.ravel())
        return hist.astype(np.float32)
    
    def _compute_color_features(self, color_img):
        hsv = cv2.cvtColor(color_img, cv2.COLOR_BGR2HSV)
        
        h_hist = cv2.calcHist([hsv], [0], None, [50], [0, 180])
        s_hist = cv2.calcHist([hsv], [1], None, [32], [0, 256])
        v_hist = cv2.calcHist([hsv], [2], None, [32], [0, 256])
        
        return np.concatenate([h_hist.flatten(), s_hist.flatten(), v_hist.flatten()])
    
    def _cosine_similarity_manual(self, vec1, vec2):
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)
    
    def set_target_object_from_image(self, input_image_path, output_folder="detected_objects", method="histogram"):
        target_id = self.find_similar_object_from_image(input_image_path, output_folder, method=method)
        if target_id:
            self.set_target_object(target_id)
            if self.verbose:
                print(f"Set target object to: {target_id} using {method} method")
            return target_id
        elif self.verbose:
            print(f"No similar object found using {method} method")
        return None
    
    def set_target_object_from_detected(self, obj_filename, output_folder="detected_objects"):
        obj_path = os.path.join(output_folder, obj_filename)
        if os.path.exists(obj_path):
            obj_id = obj_filename.split('.')[0]
            self.set_target_object(obj_id)
            
            obj_img = cv2.imread(obj_path)
            self.object_tracker.add_object_template(obj_id, obj_img)
            
            if self.verbose:
                print(f"Set target object to: {obj_id}")
            return obj_id
        return None

    def set_target_object(self, obj_id):
        self.target_object_id = obj_id
        if self.verbose:
            print(f"Target object set to: {obj_id}")
        return self
    
    def _objects_similar(self, obj1, obj2, threshold=0.6):
        if obj1.shape != obj2.shape:
            obj2 = cv2.resize(obj2, (obj1.shape[1], obj1.shape[0]))
        
        obj1_gray = cv2.cvtColor(obj1, cv2.COLOR_BGR2GRAY)
        obj2_gray = cv2.cvtColor(obj2, cv2.COLOR_BGR2GRAY)
        
        hist1 = cv2.calcHist([obj1_gray], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([obj2_gray], [0], None, [256], [0, 256])
        
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return correlation > threshold
    
    def _objects_similar_fast(self, obj1, obj2, threshold=0.45):
        if obj1.shape != obj2.shape:
            obj2 = cv2.resize(obj2, (obj1.shape[1], obj1.shape[0]))
        
        obj1_small = cv2.resize(obj1, (64, 64))
        obj2_small = cv2.resize(obj2, (64, 64))
        
        obj1_gray = cv2.cvtColor(obj1_small, cv2.COLOR_BGR2GRAY)
        obj2_gray = cv2.cvtColor(obj2_small, cv2.COLOR_BGR2GRAY)
        
        hist1 = cv2.calcHist([obj1_gray], [0], None, [32], [0, 256])
        hist2 = cv2.calcHist([obj2_gray], [0], None, [32], [0, 256])
        
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        if correlation > threshold:
            return True
        
        hsv1 = cv2.cvtColor(obj1_small, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(obj2_small, cv2.COLOR_BGR2HSV)
        
        h_hist1 = cv2.calcHist([hsv1], [0], None, [16], [0, 180])
        h_hist2 = cv2.calcHist([hsv2], [0], None, [16], [0, 180])
        
        color_correlation = cv2.compareHist(h_hist1, h_hist2, cv2.HISTCMP_CORREL)
        
        combined_score = (correlation * 0.6) + (color_correlation * 0.4)
        
        return combined_score > (threshold * 0.85)
    
    def enable_object_blur(self, blur_strength=51):
        self.enable_blur = True
        if blur_strength % 2 == 0:
            blur_strength += 1
        self.blur_strength = blur_strength
        if self.verbose:
            print(f"Object blur enabled with strength: {blur_strength}")
        return self
    
    def enable_object_zoom(self, zoom_factor=2.0):
        self.enable_zoom = True
        self.zoom_factor = zoom_factor
        if self.verbose:
            print(f"Object zoom enabled with factor: {zoom_factor}")
        return self
    
    def process_and_save(self, output_video_path):
        try:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video_path, fourcc, self.fps, (self.width, self.height))
            
            frame_count = 0
            last_detections = []
            detection_cache = {}
            
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                if frame_count % self.frame_skip == 0:
                    detections = self.detect_objects_in_frame(frame, use_small_scale=True)
                    detection_cache[frame_count] = detections
                    last_detections = detections
                else:
                    detections = last_detections
                
                frame = self._process_frame_fast(frame, detections)
                
                out.write(frame)
                frame_count += 1
                
                if self.verbose and frame_count % 60 == 0:
                    print(f"Processing: {frame_count}/{self.total_frames} frames")
            
            out.release()
            
            if self.verbose:
                print(f"Video processing completed! Output saved to: {output_video_path}")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"Error processing video: {str(e)}")
            return False
    
    def _process_frame(self, frame):
        detections = self.detect_objects_in_frame(frame, use_small_scale=False)
        
        if len(detections) == 0:
            if self.enable_zoom:
                self._handle_no_objects()
                if self.current_zoom > 1.0:
                    frame = self._apply_zoom(frame, self.prev_center_x, self.prev_center_y, self.current_zoom)
            return frame
        
        detections = sorted(detections, key=lambda d: d['bbox'][2] * d['bbox'][3], reverse=True)
        
        target_detection = None
        if self.target_object_id is not None:
            target_detection = self.object_tracker.find_target_object(detections, frame, self.target_object_id, self.detection_type)
        
        if target_detection is None:
            target_detection = detections[0]
        
        if self.enable_blur:
            self._apply_blur_to_objects(frame, detections, target_detection)
        
        if self.enable_zoom:
            frame = self._apply_zoom_to_object(frame, target_detection)
        
        return frame
    
    def _process_frame_fast(self, frame, detections):
        if len(detections) == 0:
            if self.enable_zoom:
                self._handle_no_objects()
                if self.current_zoom > 1.0:
                    frame = self._apply_zoom(frame, self.prev_center_x, self.prev_center_y, self.current_zoom)
            return frame
        
        people_detections = [d for d in detections if d['class_name'] == 'person']
        vehicle_detections = [d for d in detections if d['class_name'] in ['car', 'truck', 'bus', 'motorcycle']]
        
        if people_detections:
            people_detections = sorted(people_detections, key=lambda d: d['confidence'] * (d['bbox'][2] * d['bbox'][3]), reverse=True)
            target_detection = people_detections[0]
            
            if self.enable_blur:
                blur_kernel_size = max(5, min(51, self.blur_strength // 3))
                if blur_kernel_size % 2 == 0:
                    blur_kernel_size += 1
                
                for detection in vehicle_detections:
                    x, y, w, h = detection['bbox']
                    x, y = max(0, x), max(0, y)
                    w = min(w, frame.shape[1] - x)
                    h = min(h, frame.shape[0] - y)
                    
                    if w > 0 and h > 0:
                        obj_region = frame[y:y+h, x:x+w]
                        blurred_obj = cv2.GaussianBlur(obj_region, (blur_kernel_size, blur_kernel_size), 0)
                        frame[y:y+h, x:x+w] = blurred_obj
            
            if self.enable_zoom:
                frame = self._apply_zoom_to_object_smooth(frame, target_detection)
        elif vehicle_detections and not people_detections:
            largest_vehicle = max(vehicle_detections, key=lambda d: d['bbox'][2] * d['bbox'][3])
            if self.enable_zoom:
                frame = self._apply_zoom_to_object_smooth(frame, largest_vehicle)
        
        return frame
    
    def _handle_no_objects(self):
        decay_rate = 0.92
        center_pull = 0.02
        
        self.current_zoom = max(1.0, self.current_zoom * decay_rate)
        self.zoom_momentum *= 0.9
        
        self.prev_center_x = int((1 - center_pull) * self.prev_center_x + center_pull * (self.width // 2))
        self.prev_center_y = int((1 - center_pull) * self.prev_center_y + center_pull * (self.height // 2))
    
    def _apply_blur_to_objects(self, frame, detections, target_detection):
        if self.target_object_id is not None:
            for detection in detections:
                if detection != target_detection:
                    x, y, w, h = detection['bbox']
                    obj_region = frame[y:y+h, x:x+w]
                    blurred_obj = cv2.GaussianBlur(obj_region, (self.blur_strength, self.blur_strength), 0)
                    frame[y:y+h, x:x+w] = blurred_obj
        else:
            for detection in detections:
                x, y, w, h = detection['bbox']
                obj_region = frame[y:y+h, x:x+w]
                blurred_obj = cv2.GaussianBlur(obj_region, (self.blur_strength, self.blur_strength), 0)
                frame[y:y+h, x:x+w] = blurred_obj
    
    def _apply_blur_to_objects_fast(self, frame, detections, target_detection):
        blur_kernel = (self.blur_strength//2, self.blur_strength//2)
        if self.target_object_id is not None:
            for detection in detections:
                if detection != target_detection:
                    x, y, w, h = detection['bbox']
                    obj_region = frame[y:y+h, x:x+w]
                    blurred_obj = cv2.blur(obj_region, blur_kernel)
                    frame[y:y+h, x:x+w] = blurred_obj
        else:
            for detection in detections:
                x, y, w, h = detection['bbox']
                obj_region = frame[y:y+h, x:x+w]
                blurred_obj = cv2.blur(obj_region, blur_kernel)
                frame[y:y+h, x:x+w] = blurred_obj
    
    def _apply_zoom_to_object(self, frame, target_detection):
        x, y, w, h = target_detection['bbox']
        obj_center_x = x + w // 2
        obj_center_y = y + h // 2
        
        center_diff_x = obj_center_x - self.prev_center_x
        center_diff_y = obj_center_y - self.prev_center_y
        distance = np.sqrt(center_diff_x**2 + center_diff_y**2)
        
        if distance > 50:
            momentum_factor = min(0.3, distance / 200)
        else:
            momentum_factor = 0.08
        
        self.zoom_momentum = 0.85 * self.zoom_momentum + 0.15 * momentum_factor
        effective_smoothing = max(0.05, min(0.25, self.zoom_momentum))
        
        target_center_x = int((1 - effective_smoothing) * self.prev_center_x + effective_smoothing * obj_center_x)
        target_center_y = int((1 - effective_smoothing) * self.prev_center_y + effective_smoothing * obj_center_y)
        
        zoom_smoothing = 0.12
        target_zoom = (1 - zoom_smoothing) * self.current_zoom + zoom_smoothing * self.zoom_factor
        
        self.prev_center_x = target_center_x
        self.prev_center_y = target_center_y
        self.current_zoom = target_zoom
        
        return self._apply_zoom(frame, target_center_x, target_center_y, self.current_zoom)
    
    def _apply_zoom_to_object_smooth(self, frame, target_detection):
        x, y, w, h = target_detection['bbox']
        obj_center_x = x + w // 2
        obj_center_y = y + h // 2
        
        smoothing_factor = 0.15
        
        target_center_x = int((1 - smoothing_factor) * self.prev_center_x + smoothing_factor * obj_center_x)
        target_center_y = int((1 - smoothing_factor) * self.prev_center_y + smoothing_factor * obj_center_y)
        
        zoom_smoothing = 0.08
        target_zoom = (1 - zoom_smoothing) * self.current_zoom + zoom_smoothing * self.zoom_factor
        
        self.prev_center_x = target_center_x
        self.prev_center_y = target_center_y
        self.current_zoom = target_zoom
        
        return self._apply_zoom(frame, target_center_x, target_center_y, self.current_zoom)
    
    def _apply_zoom(self, frame, center_x, center_y, zoom_factor):
        crop_width = int(self.width / zoom_factor)
        crop_height = int(self.height / zoom_factor)
        
        crop_x = max(0, min(center_x - crop_width // 2, self.width - crop_width))
        crop_y = max(0, min(center_y - crop_height // 2, self.height - crop_height))
        
        cropped_frame = frame[crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
        return cv2.resize(cropped_frame, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
    
    def __del__(self):
        if hasattr(self, 'cap'):
            self.cap.release()