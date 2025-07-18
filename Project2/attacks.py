import cv2
import numpy as np

def apply_attacks(img):
    attacked_images = []

    attacked_images.append(("水平翻转", cv2.flip(img, 1)))
    attacked_images.append(("垂直翻转", cv2.flip(img, 0)))

    M = np.float32([[1, 0, 50], [0, 1, 50]])
    attacked_images.append(("平移", cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))))

    h, w = img.shape[:2]
    cropped = img[h//4:3*h//4, w//4:3*w//4]
    attacked_images.append(("裁剪", cropped))

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l_contrast = clahe.apply(l)
    contrast = cv2.merge([l_contrast, a, b])
    attacked_images.append(("对比度增强", cv2.cvtColor(contrast, cv2.COLOR_LAB2BGR)))

    noise = np.zeros_like(img)
    cv2.randn(noise, 0, 25)
    attacked_images.append(("高斯噪声", cv2.add(img, noise)))

    _, jpeg = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
    jpeg_img = cv2.imdecode(jpeg, 1)
    attacked_images.append(("JPEG压缩", jpeg_img))

    return attacked_images
