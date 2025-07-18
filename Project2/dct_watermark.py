import cv2
import numpy as np

class DCTWatermark:
    def __init__(self, strength=25.0):
        self.strength = strength

    def _preprocess_watermark(self, watermark, target_shape):
        wm_resized = cv2.resize(watermark, (target_shape[1], target_shape[0]))
        _, wm_binary = cv2.threshold(wm_resized, 128, 1, cv2.THRESH_BINARY)
        return wm_binary

    def embed(self, host_img, watermark_img):
        yuv = cv2.cvtColor(host_img, cv2.COLOR_BGR2YUV)
        y, u, v = cv2.split(yuv)
        y_float = np.float32(y)
        wm_binary = self._preprocess_watermark(watermark_img, y.shape)

        blocks = []
        for i in range(0, y.shape[0], 8):
            for j in range(0, y.shape[1], 8):
                block = y_float[i:i+8, j:j+8]
                if block.shape == (8, 8):
                    dct_block = cv2.dct(block)
                    if i//8 < wm_binary.shape[0] and j//8 < wm_binary.shape[1]:
                        bit = wm_binary[i//8, j//8]
                        if bit == 1:
                            dct_block[5, 2] += self.strength
                            dct_block[4, 3] += self.strength
                        else:
                            dct_block[5, 2] -= self.strength
                            dct_block[4, 3] -= self.strength
                    blocks.append(cv2.idct(dct_block))

        watermarked_y = np.zeros_like(y_float)
        idx = 0
        for i in range(0, y.shape[0], 8):
            for j in range(0, y.shape[1], 8):
                if i+8 <= y.shape[0] and j+8 <= y.shape[1]:
                    watermarked_y[i:i+8, j:j+8] = blocks[idx]
                    idx += 1

        watermarked_y = np.uint8(np.clip(watermarked_y, 0, 255))
        merged = cv2.merge([watermarked_y, u, v])
        return cv2.cvtColor(merged, cv2.COLOR_YUV2BGR)

    def extract(self, watermarked_img, original_shape):
        yuv = cv2.cvtColor(watermarked_img, cv2.COLOR_BGR2YUV)
        y_float = np.float32(yuv[:, :, 0])
        extracted = np.zeros(original_shape, dtype=np.uint8)
        for i in range(0, y_float.shape[0], 8):
            for j in range(0, y_float.shape[1], 8):
                if i//8 < original_shape[0] and j//8 < original_shape[1]:
                    block = y_float[i:i+8, j:j+8]
                    if block.shape == (8, 8):
                        dct_block = cv2.dct(block)
                        avg_val = (dct_block[5, 2] + dct_block[4, 3]) / 2
                        extracted[i//8, j//8] = 255 if avg_val > 0 else 0
        return extracted
