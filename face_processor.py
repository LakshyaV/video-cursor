import cv2
import numpy as np
import os
import glob
from collections import defaultdict

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

class FaceTracker:
    def __init__(self):
        self.face_templates = {}
        self.face_centers_history = defaultdict(list)
    
    def add_face_template(self, face_id, face_img):
        self.face_templates[face_id] = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    
    def find_target_face(self, faces, frame, target_face_id):
        if target_face_id is None or target_face_id not in self.face_templates:
            return faces[0] if faces else None
        
        template = self.face_templates[target_face_id]
        best_match = None
        best_score = 0
        
        for (x, y, w, h) in faces:
            face_region = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
            face_resized = cv2.resize(face_region, (template.shape[1], template.shape[0]))
            
            hist1 = cv2.calcHist([template], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([face_resized], [0], None, [256], [0, 256])
            score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            if score > best_score and score > 0.6:
                best_score = score
                best_match = (x, y, w, h)
        
        return best_match

class FaceProcessor:
    def __init__(self, input_video_path, verbose=False):
        self.input_video_path = input_video_path
        self.verbose = verbose
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        self.cap = cv2.VideoCapture(input_video_path)
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        self.enable_blur = False
        self.enable_zoom = False
        self.blur_strength = 51
        self.zoom_factor = 2.0
        self.target_face_id = None
        
        self.prev_center_x = self.width // 2
        self.prev_center_y = self.height // 2
        self.current_zoom = 1.0
        self.zoom_momentum = 0.0
        
        self.face_tracker = FaceTracker()
        
        if self.verbose:
            print(f"Loaded video: {input_video_path}")
            print(f"Resolution: {self.width}x{self.height}, FPS: {self.fps}, Frames: {self.total_frames}")
    
    def extract_faces(self, output_folder="detected_faces", sample_frames=30):
        if os.path.exists(output_folder):
            import shutil
            shutil.rmtree(output_folder)
        os.makedirs(output_folder, exist_ok=True)
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        unique_faces = {}
        face_id_counter = 0
        frame_interval = max(1, self.total_frames // sample_frames)
        
        if self.verbose:
            print(f"Extracting faces from video (sampling every {frame_interval} frames)...")
        
        frame_count = 0
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                for (x, y, w, h) in faces:
                    face_img = frame[y:y+h, x:x+w]
                    
                    is_new_face = True
                    for face_id, stored_face in unique_faces.items():
                        if self._faces_similar(face_img, stored_face):
                            is_new_face = False
                            break
                    
                    if is_new_face:
                        face_path = os.path.join(output_folder, f"face_{face_id_counter}.jpg")
                        cv2.imwrite(face_path, face_img)
                        unique_faces[face_id_counter] = face_img
                        face_id_counter += 1
                        
                        if self.verbose:
                            print(f"Found new face: face_{face_id_counter-1}.jpg")
            
            frame_count += 1
        
        if self.verbose:
            print(f"Extracted {len(unique_faces)} unique faces to '{output_folder}' folder")
        
        return list(unique_faces.keys())
    
    def get_detected_faces(self, output_folder="detected_faces"):
        if not os.path.exists(output_folder):
            return []
        
        face_files = glob.glob(os.path.join(output_folder, "face_*.jpg"))
        return sorted(face_files)
    
    def find_similar_face_from_image(self, input_image_path, output_folder="detected_faces", threshold=0.6, method="embedding"):
        if isinstance(input_image_path, str):
            query_img = cv2.imread(input_image_path)
        else:
            query_img = input_image_path
        
        if query_img is None:
            return None
        
        if method == "embedding" and FACE_RECOGNITION_AVAILABLE:
            return self._find_similar_face_embedding(query_img, output_folder, threshold)
        elif method == "cosine":
            return self._find_similar_face_cosine(query_img, output_folder, threshold)
        else:
            return self._find_similar_face_histogram(query_img, output_folder, threshold)
    
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
        
        detected_faces = self.get_detected_faces(output_folder)
        
        for face_path in detected_faces:
            face_img = cv2.imread(face_path)
            if face_img is None:
                continue
            
            face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(face_rgb)
            
            if not face_encodings:
                continue
            
            face_encoding = face_encodings[0]
            distance = face_recognition.face_distance([query_encoding], face_encoding)[0]
            
            if distance < best_distance and distance < threshold:
                best_distance = distance
                best_match = os.path.basename(face_path).split('.')[0]
        
        if self.verbose and best_match:
            print(f"Best face match: {best_match} with distance: {best_distance:.3f}")
        
        return best_match
    
    def _find_similar_face_histogram(self, query_img, output_folder, threshold):
        query_gray = cv2.cvtColor(query_img, cv2.COLOR_BGR2GRAY)
        query_hist = cv2.calcHist([query_gray], [0], None, [256], [0, 256])
        
        best_match = None
        best_score = 0
        
        detected_faces = self.get_detected_faces(output_folder)
        
        for face_path in detected_faces:
            face_img = cv2.imread(face_path)
            if face_img is None:
                continue
            
            face_gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            face_resized = cv2.resize(face_gray, (query_gray.shape[1], query_gray.shape[0]))
            face_hist = cv2.calcHist([face_resized], [0], None, [256], [0, 256])
            
            score = cv2.compareHist(query_hist, face_hist, cv2.HISTCMP_CORREL)
            
            if score > best_score and score > threshold:
                best_score = score
                best_match = os.path.basename(face_path).split('.')[0]
        
        return best_match
    
    def _find_similar_face_cosine(self, query_img, output_folder, threshold):
        query_features = self._extract_face_features(query_img)
        if query_features is None:
            return None
        
        best_match = None
        best_score = 0
        
        detected_faces = self.get_detected_faces(output_folder)
        
        for face_path in detected_faces:
            face_img = cv2.imread(face_path)
            if face_img is None:
                continue
            
            face_features = self._extract_face_features(face_img)
            if face_features is None:
                continue
            
            if SKLEARN_AVAILABLE:
                score = cosine_similarity([query_features], [face_features])[0][0]
            else:
                score = self._cosine_similarity_manual(query_features, face_features)
            
            if score > best_score and score > threshold:
                best_score = score
                best_match = os.path.basename(face_path).split('.')[0]
        
        return best_match
    
    def _extract_face_features(self, face_img):
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (64, 64))
        
        lbp_features = self._compute_lbp(resized)
        hog_features = self._compute_hog(resized)
        color_features = self._compute_color_features(face_img)
        
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
    
    def set_target_face_from_image(self, input_image_path, output_folder="detected_faces", method="embedding"):
        target_id = self.find_similar_face_from_image(input_image_path, output_folder, method=method)
        if target_id:
            self.set_target_face(target_id)
            if self.verbose:
                print(f"Set target face to: {target_id} using {method} method")
            return target_id
        elif self.verbose:
            print(f"No similar face found using {method} method")
        return None
    
    def set_target_face_from_detected(self, face_filename, output_folder="detected_faces"):
        face_path = os.path.join(output_folder, face_filename)
        if os.path.exists(face_path):
            face_id = face_filename.split('.')[0]
            self.set_target_face(face_id)
            
            face_img = cv2.imread(face_path)
            self.face_tracker.add_face_template(face_id, face_img)
            
            if self.verbose:
                print(f"Set target face to: {face_id}")
            return face_id
        return None

    def set_target_face(self, face_id):
        self.target_face_id = face_id
        if self.verbose:
            print(f"Target face set to: {face_id}")
        return self
    
    def _faces_similar(self, face1, face2, threshold=0.6):
        if face1.shape != face2.shape:
            face2 = cv2.resize(face2, (face1.shape[1], face1.shape[0]))
        
        face1_gray = cv2.cvtColor(face1, cv2.COLOR_BGR2GRAY)
        face2_gray = cv2.cvtColor(face2, cv2.COLOR_BGR2GRAY)
        
        hist1 = cv2.calcHist([face1_gray], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([face2_gray], [0], None, [256], [0, 256])
        
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return correlation > threshold
    
    def enable_face_blur(self, blur_strength=51):
        self.enable_blur = True
        if blur_strength % 2 == 0:
            blur_strength += 1
        self.blur_strength = blur_strength
        if self.verbose:
            print(f"Face blur enabled with strength: {blur_strength}")
        return self
    
    def enable_face_zoom(self, zoom_factor=2.0):
        self.enable_zoom = True
        self.zoom_factor = zoom_factor
        if self.verbose:
            print(f"Face zoom enabled with factor: {zoom_factor}")
        return self
    
    def process_and_save(self, output_video_path):
        try:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video_path, fourcc, self.fps, (self.width, self.height))
            
            frame_count = 0
            
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                frame = self._process_frame(frame)
                
                out.write(frame)
                frame_count += 1
                
                if self.verbose and frame_count % 30 == 0:
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
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=6, minSize=(30, 30))
        
        if len(faces) == 0:
            if self.enable_zoom:
                self._handle_no_faces()
                if self.current_zoom > 1.0:
                    frame = self._apply_zoom(frame, self.prev_center_x, self.prev_center_y, self.current_zoom)
            return frame
        
        faces = sorted(faces, key=lambda face: face[2] * face[3], reverse=True)
        
        target_face = None
        if self.target_face_id is not None:
            target_face = self.face_tracker.find_target_face(faces, frame, self.target_face_id)
        
        if target_face is None:
            target_face = faces[0]
        
        if self.enable_blur:
            self._apply_blur_to_faces(frame, faces, target_face)
        
        if self.enable_zoom:
            frame = self._apply_zoom_to_face(frame, target_face)
        
        return frame
    
    def _handle_no_faces(self):
        decay_rate = 0.92
        center_pull = 0.02
        
        self.current_zoom = max(1.0, self.current_zoom * decay_rate)
        self.zoom_momentum *= 0.9
        
        self.prev_center_x = int((1 - center_pull) * self.prev_center_x + center_pull * (self.width // 2))
        self.prev_center_y = int((1 - center_pull) * self.prev_center_y + center_pull * (self.height // 2))
    
    def _apply_blur_to_faces(self, frame, faces, target_face):
        if self.target_face_id is not None:
            for (x, y, w, h) in faces:
                if (x, y, w, h) != target_face:
                    face_region = frame[y:y+h, x:x+w]
                    blurred_face = cv2.GaussianBlur(face_region, (self.blur_strength, self.blur_strength), 0)
                    frame[y:y+h, x:x+w] = blurred_face
        else:
            for (x, y, w, h) in faces:
                face_region = frame[y:y+h, x:x+w]
                blurred_face = cv2.GaussianBlur(face_region, (self.blur_strength, self.blur_strength), 0)
                frame[y:y+h, x:x+w] = blurred_face
    
    def _apply_zoom_to_face(self, frame, target_face):
        x, y, w, h = target_face
        face_center_x = x + w // 2
        face_center_y = y + h // 2
        
        center_diff_x = face_center_x - self.prev_center_x
        center_diff_y = face_center_y - self.prev_center_y
        distance = np.sqrt(center_diff_x**2 + center_diff_y**2)
        
        if distance > 50:
            momentum_factor = min(0.3, distance / 200)
        else:
            momentum_factor = 0.08
        
        self.zoom_momentum = 0.85 * self.zoom_momentum + 0.15 * momentum_factor
        effective_smoothing = max(0.05, min(0.25, self.zoom_momentum))
        
        target_center_x = int((1 - effective_smoothing) * self.prev_center_x + effective_smoothing * face_center_x)
        target_center_y = int((1 - effective_smoothing) * self.prev_center_y + effective_smoothing * face_center_y)
        
        zoom_smoothing = 0.12
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