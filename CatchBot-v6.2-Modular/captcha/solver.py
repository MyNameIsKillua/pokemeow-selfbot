#!/usr/bin/env python3
"""
CatchBot CAPTCHA AI Solver - ONNX Edition (Nuitka Compatible)
Uses ONLY onnxruntime + numpy + pillow - NO torch/transformers needed!

REQUIREMENTS (for .exe):
  pip install onnxruntime numpy pillow cryptography

USAGE:
  python solve_captcha.py image.png              - Solve single
  python solve_captcha.py Captcha/               - Solve folder
  python solve_captcha.py Captcha/ --test        - Test accuracy
"""

import os
import sys
import json
import time
import numpy as np
from PIL import Image
from io import BytesIO
import base64

# Runtime dependencies only - NO torch!
import onnxruntime as ort
from cryptography.fernet import Fernet

MODEL_PATH = "catchbot_model_onnx"
ENCRYPTION_KEY = b'ODmJlL7HRMdOcAlaj7M752GftdNyZPtOFEAwkaU9_Ts='


class CaptchaAISolver:
    """
    ONNX-based captcha solver - lightweight, Nuitka compatible.
    
    Usage:
        solver = CaptchaAISolver()
        answer = solver.solve_from_file("captcha.png")
        answer = solver.solve_from_bytes(raw_bytes)
        answer = solver.solve_from_base64(b64_string)
    """

    def __init__(self, model_path=MODEL_PATH):
        print("Loading AI model (ONNX)...")

        encrypted_dir = model_path + "_encrypted"
        
        if os.path.exists(encrypted_dir):
            if not ENCRYPTION_KEY:
                raise ValueError("Model is encrypted but ENCRYPTION_KEY not set!")
            self._load_encrypted(encrypted_dir)
        elif os.path.exists(model_path):
            self._load_from_dir(model_path)
        else:
            raise FileNotFoundError(
                "Model not found: '%s' or '%s'" % (model_path, encrypted_dir)
            )

        # Determine device
        providers = self.enc_session.get_providers()
        if "CUDAExecutionProvider" in providers:
            self.device = "CUDA"
        else:
            self.device = "CPU"

        print("CatchBot AI Solver v8 (ONNX) loaded! Device: %s" % self.device)

    def _load_from_dir(self, model_dir):
        """Load ONNX models from directory"""
        # Load config
        cfg_path = os.path.join(model_dir, "catchbot_config.json")
        with open(cfg_path, "r") as f:
            self.config = json.load(f)

        # Suppress noisy CUDA fallback warnings when GPU is not available
        ort.set_default_logger_severity(4)  # FATAL only
        
        # Session options
        sess_opts = ort.SessionOptions()
        sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_opts.log_severity_level = 4

        # Providers - request CUDA but silently fall back to CPU
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

        # Temporarily redirect stderr at OS level during session creation
        # (ONNX native C++ layer prints CUDA errors to file descriptor 2 directly)
        _old_stderr = None
        try:
            _stderr_fd = sys.stderr.fileno()
            _old_stderr = os.dup(_stderr_fd)
            _devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(_devnull, _stderr_fd)
            os.close(_devnull)
        except Exception:
            _old_stderr = None  # fileno() may fail in some environments

        try:
            # Load encoder
            enc_path = os.path.join(model_dir, "encoder_model.onnx")
            self.enc_session = ort.InferenceSession(enc_path, sess_opts, providers=providers)

            # Load decoder
            dec_path = os.path.join(model_dir, "decoder_model.onnx")
            self.dec_session = ort.InferenceSession(dec_path, sess_opts, providers=providers)
        finally:
            if _old_stderr is not None:
                os.dup2(_old_stderr, sys.stderr.fileno())
                os.close(_old_stderr)

        # Store config values
        self.decoder_start_id = self.config["decoder_start_token_id"]
        self.eos_token_id = self.config["eos_token_id"]
        self.max_length = self.config["max_length"]
        self.img_h = self.config["image_height"]
        self.img_w = self.config["image_width"]
        self.image_mean = np.array(self.config["image_mean"], dtype=np.float32)
        self.image_std = np.array(self.config["image_std"], dtype=np.float32)
        self.digit_vocab = self.config.get("digit_vocab", {})

    def _load_encrypted(self, encrypted_dir):
        """Decrypt and load models"""
        import tempfile
        import shutil

        cipher = Fernet(ENCRYPTION_KEY)
        self.temp_dir = tempfile.mkdtemp(prefix="catchbot_")

        print("  Decrypting model files...")

        # Decrypt all .enc files
        for fname in os.listdir(encrypted_dir):
            if fname.endswith(".enc"):
                src_path = os.path.join(encrypted_dir, fname)
                dst_name = fname[:-4]  # Remove .enc
                dst_path = os.path.join(self.temp_dir, dst_name)

                with open(src_path, "rb") as f:
                    encrypted_data = f.read()

                decrypted_data = cipher.decrypt(encrypted_data)

                with open(dst_path, "wb") as f:
                    f.write(decrypted_data)

        self._load_from_dir(self.temp_dir)

    def _preprocess(self, image):
        """Preprocess image to model input format"""
        # Convert to RGB
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Resize
        image = image.resize((self.img_w, self.img_h), Image.BILINEAR)

        # Convert to numpy array
        img_array = np.array(image, dtype=np.float32) / 255.0

        # Normalize: (img - mean) / std
        img_array = (img_array - self.image_mean) / self.image_std

        # HWC -> CHW
        img_array = np.transpose(img_array, (2, 0, 1))

        # Add batch dimension: (1, 3, H, W)
        img_array = np.expand_dims(img_array, axis=0)

        return img_array.astype(np.float32)

    def _decode_tokens(self, token_ids):
        """Extract digits from token IDs"""
        result = ""
        for tid in token_ids:
            token_str = self.digit_vocab.get(str(int(tid)), "")
            for c in token_str:
                if c.isdigit():
                    result += c
        return result

    def _generate(self, pixel_values):
        """Run inference with greedy decoding"""
        # Encoder forward pass
        encoder_out = self.enc_session.run(
            None, {"pixel_values": pixel_values}
        )[0]

        # Start with decoder_start_token
        generated = [self.decoder_start_id]

        # Autoregressive generation
        for _ in range(self.max_length + 2):
            # Prepare input_ids as numpy array
            input_ids = np.array([generated], dtype=np.int64)

            # Decoder forward pass
            logits = self.dec_session.run(
                None,
                {
                    "input_ids": input_ids,
                    "encoder_hidden_states": encoder_out,
                },
            )[0]  # Shape: (1, seq_len, vocab_size)

            # Get next token from last position
            next_token = int(np.argmax(logits[0, -1, :]))

            # Check for EOS
            if next_token == self.eos_token_id:
                break

            generated.append(next_token)

        # Skip decoder_start_token and decode
        return self._decode_tokens(generated[1:])

    def _predict(self, image):
        """Single prediction"""
        pixel_values = self._preprocess(image)
        return self._generate(pixel_values)

    def solve_from_file(self, path, use_tta=False):
        """Solve captcha from file path"""
        image = Image.open(path)
        if use_tta:
            return self._predict_with_tta(image)
        return self._predict(image)

    def solve_from_bytes(self, data, use_tta=False):
        """Solve captcha from bytes"""
        image = Image.open(BytesIO(data))
        if use_tta:
            return self._predict_with_tta(image)
        return self._predict(image)

    def solve_from_base64(self, b64_string, use_tta=False):
        """Solve captcha from base64 string"""
        if b64_string.startswith("data:"):
            b64_string = b64_string.split(",", 1)[-1]
        data = base64.b64decode(b64_string)
        return self.solve_from_bytes(data, use_tta)

    def _predict_with_tta(self, image):
        """Test-time augmentation"""
        from collections import Counter
        
        predictions = [self._predict(image)]

        # Slight rotations
        for angle in [-2, 2]:
            try:
                rotated = image.rotate(angle, fillcolor=(255, 255, 255))
                predictions.append(self._predict(rotated))
            except:
                pass

        # Return most common prediction
        counter = Counter(predictions)
        return counter.most_common(1)[0][0]

    def __del__(self):
        """Cleanup temp directory"""
        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: python solve_captcha.py <image.png | Captcha/> [--test] [--tta]")
        sys.exit(1)

    path = sys.argv[1]
    test_mode = "--test" in sys.argv
    use_tta = "--tta" in sys.argv

    # Check model exists
    encrypted_path = MODEL_PATH + "_encrypted"
    if not os.path.exists(MODEL_PATH) and not os.path.exists(encrypted_path):
        print("Error: Model not found at '%s'" % MODEL_PATH)
        print("Run export_to_onnx.py first!")
        sys.exit(1)

    solver = CaptchaAISolver(MODEL_PATH)

    if use_tta:
        print("  TTA mode: ON")
    print()

    # Single file
    if os.path.isfile(path):
        result = solver.solve_from_file(path, use_tta)
        print("Prediction: %s" % result)

    # Directory
    elif os.path.isdir(path):
        # Get all image files
        image_files = sorted([
            os.path.join(path, f) for f in os.listdir(path)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
            and not f.startswith("unlabeled_")
        ])

        if not image_files:
            print("No images found in %s" % path)
            return

        print("Processing %d images...\n" % len(image_files))

        correct = 0
        total = 0
        wrong = []
        t_start = time.time()
        last_print = t_start

        for idx, img_path in enumerate(image_files):
            fname = os.path.basename(img_path)
            
            # Get expected label from filename (e.g., "123456_xxx.png" -> "123456")
            expected = fname.split("_")[0]
            
            result = solver.solve_from_file(img_path, use_tta)

            if test_mode:
                is_correct = result == expected
                correct += int(is_correct)
                total += 1
                
                if not is_correct:
                    wrong.append((expected, result, fname))

            # Progress update
            now = time.time()
            if (now - last_print >= 2.0) or (idx + 1 == len(image_files)):
                elapsed = now - t_start
                speed = (idx + 1) / elapsed if elapsed > 0 else 0
                pct = (idx + 1) / len(image_files) * 100
                eta = (len(image_files) - idx - 1) / speed if speed > 0 else 0
                
                if test_mode and total > 0:
                    acc = correct / total * 100
                    print("[%d/%d] %.0f%% | %.1f img/s | ETA: %ds | Acc: %.1f%%    " % (
                        idx + 1, len(image_files), pct, speed, int(eta), acc
                    ), end="\r")
                else:
                    print("[%d/%d] %.0f%% | %.1f img/s | ETA: %ds    " % (
                        idx + 1, len(image_files), pct, speed, int(eta)
                    ), end="\r")
                
                last_print = now

        elapsed = time.time() - t_start
        print()

        if test_mode and total > 0:
            accuracy = correct / total * 100
            print()
            print("=" * 60)
            print("RESULTS")
            print("=" * 60)
            print("Accuracy: %d/%d = %.2f%%" % (correct, total, accuracy))
            print("Speed: %.1f img/s (%.1fs total)" % (total / elapsed, elapsed))
            
            if wrong:
                print()
                print("Wrong predictions (%d):" % len(wrong))
                for expected, result, fname in wrong[:20]:
                    print("  %s: got '%s', expected '%s'" % (fname, result, expected))
                if len(wrong) > 20:
                    print("  ... and %d more" % (len(wrong) - 20))

            # Accuracy by digit length
            length_stats = {}
            for img_path in image_files:
                fname = os.path.basename(img_path)
                expected = fname.split("_")[0]
                l = len(expected)
                if l not in length_stats:
                    length_stats[l] = {"total": 0, "wrong": 0}
                length_stats[l]["total"] += 1
            
            for expected, result, fname in wrong:
                l = len(expected)
                length_stats[l]["wrong"] += 1

            print()
            print("By digit length:")
            for l in sorted(length_stats.keys()):
                stats = length_stats[l]
                correct_l = stats["total"] - stats["wrong"]
                acc_l = correct_l / stats["total"] * 100 if stats["total"] > 0 else 0
                print("  %d digits: %d/%d = %.1f%%" % (l, correct_l, stats["total"], acc_l))

    else:
        print("Error: %s not found" % path)
        sys.exit(1)


if __name__ == "__main__":
    main()