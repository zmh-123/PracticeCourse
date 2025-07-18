import cv2
import numpy as np

def calculate_similarity(original_wm, extracted_wm):
    if original_wm.shape != extracted_wm.shape:
        extracted_wm = cv2.resize(extracted_wm, (original_wm.shape[1], original_wm.shape[0]))
    intersection = np.logical_and(original_wm, extracted_wm)
    union = np.logical_or(original_wm, extracted_wm)
    similarity = np.sum(intersection) / np.sum(union)
    return similarity * 100
