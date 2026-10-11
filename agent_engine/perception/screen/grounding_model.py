from __future__ import annotations

import re
import time

import torch
from PIL import Image

from transformers import (
    AutoProcessor,
    Qwen2VLForConditionalGeneration,
)


class ScreenGroundingModel:

    MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
    ):

        self.model_name = model_name or self.MODEL_NAME

        self.device = device or (
            "cuda:0" if torch.cuda.is_available() else "cpu"
        )

        self.dtype = (
            torch.float16
            if torch.cuda.is_available()
            else torch.float32
        )

        self.processor = None
        self.model = None
        self.loaded = False

    # ---------------------------------------------------------
    # MODEL LOADING
    # ---------------------------------------------------------

    def load(self):
        """
        Load processor + Qwen model exactly once.
        """

        if self.loaded:
            return

        print()
        print("=" * 60)
        print("SCREEN GROUNDING MODEL")
        print("=" * 60)

        print(f"Model : {self.model_name}")
        print(f"Device: {self.device}")
        print(f"Dtype : {self.dtype}")

        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            min_pixels=256 * 256,
            max_pixels=1280 * 720,
        )

        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_name,
            torch_dtype=self.dtype,
            device_map={"": self.device},
            low_cpu_mem_usage=True,
        )

        self.model.eval()

        self.loaded = True

        if torch.cuda.is_available():

            print(
                f"GPU: {torch.cuda.get_device_name(0)}"
            )

            print(
                f"VRAM allocated: "
                f"{torch.cuda.memory_allocated() / 1024**3:.2f} GB"
            )

        print("Qwen2-VL loaded successfully.")
        print("=" * 60)

        # Small warm-up.
        self._warmup()

    # ---------------------------------------------------------
    # WARMUP
    # ---------------------------------------------------------

    def _warmup(self):

        if not self.loaded:
            return

        try:

            dummy = Image.new(
                "RGB",
                (320, 240),
                "white",
            )

            self._locate_qwen(
                dummy,
                "nonexistent test element",
            )

            if torch.cuda.is_available():
                torch.cuda.synchronize()

            print("[SCREEN] Qwen warm-up complete.")

        except Exception as exc:

            print(
                f"[SCREEN] Warm-up warning: {exc}"
            )

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------

    def locate(
        self,
        image: Image.Image,
        query: str,
    ):

        if not self.loaded:
            self.load()

        return self._locate_qwen(
            image,
            query,
        )

    # ---------------------------------------------------------
    # QWEN INFERENCE
    # ---------------------------------------------------------

    @torch.inference_mode()
    def _locate_qwen(
        self,
        image: Image.Image,
        query: str,
    ):

        start = time.perf_counter()

        if image.mode != "RGB":
            image = image.convert("RGB")

        original_width, original_height = image.size

        # Keep visual input reasonably small.
        max_dimension = 1280

        scale = min(
            1.0,
            max_dimension / max(
                original_width,
                original_height,
            ),
        )

        if scale < 1.0:

            resized = image.resize(
                (
                    int(original_width * scale),
                    int(original_height * scale),
                )
            )

        else:
            resized = image

        prompt = f"""
Locate the UI element requested by the user.

Target:
{query}

Return ONLY four integers:

x1 y1 x2 y2

The coordinates must describe the bounding box of the target.

If the target cannot be found, return:
-1 -1 -1 -1

Do not explain anything.
"""

        inputs = self.processor(
            text=prompt,
            images=resized,
            return_tensors="pt",
        )

        inputs = {
            key: value.to(self.device)
            if hasattr(value, "to")
            else value
            for key, value in inputs.items()
        }

        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=16,
            do_sample=False,
        )

        output_ids = generated_ids[
            :, inputs["input_ids"].shape[1]:
        ]

        output = self.processor.batch_decode(
            output_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )[0].strip()

        numbers = re.findall(
            r"-?\d+",
            output,
        )

        if len(numbers) < 4:

            return {
                "found": False,
                "query": query,
                "coordinates": None,
                "bbox": None,
                "confidence": 0.0,
                "method": "Qwen2-VL",
                "latency_ms": (
                    time.perf_counter() - start
                ) * 1000,
                "raw_output": output,
            }

        x1, y1, x2, y2 = map(
            int,
            numbers[:4],
        )

        if x1 < 0 or y1 < 0 or x2 < 0 or y2 < 0:

            return {
                "found": False,
                "query": query,
                "coordinates": None,
                "bbox": None,
                "confidence": 0.0,
                "method": "Qwen2-VL",
                "latency_ms": (
                    time.perf_counter() - start
                ) * 1000,
                "raw_output": output,
            }

        # Coordinates are assumed to be normalized
        # to a 0-1000 visual coordinate system.

        x1 = int(
            x1 * original_width / 1000
        )

        y1 = int(
            y1 * original_height / 1000
        )

        x2 = int(
            x2 * original_width / 1000
        )

        y2 = int(
            y2 * original_height / 1000
        )

        # Clamp.
        x1 = max(0, min(x1, original_width))
        y1 = max(0, min(y1, original_height))
        x2 = max(0, min(x2, original_width))
        y2 = max(0, min(y2, original_height))

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        latency = (
            time.perf_counter() - start
        ) * 1000

        return {
            "found": True,
            "query": query,
            "coordinates": {
                "x": center_x,
                "y": center_y,
            },
            "bbox": [
                x1,
                y1,
                x2,
                y2,
            ],
            "confidence": None,
            "method": "Qwen2-VL",
            "latency_ms": latency,
            "raw_output": output,
        }