import cv2
import os
import matplotlib.pyplot as plt
from dct_watermark import DCTWatermark
from attacks import apply_attacks
from metrics import calculate_similarity

# 创建输出目录
os.makedirs('output', exist_ok=True)

host = cv2.imread('images/host_image.jpg')
watermark = cv2.imread('images/watermark.png', cv2.IMREAD_GRAYSCALE)

wm_sys = DCTWatermark(strength=30.0)
watermarked = wm_sys.embed(host, watermark)
cv2.imwrite('output/watermarked.jpg', watermarked)

original_shape = watermark.shape
extracted_original = wm_sys.extract(watermarked, original_shape)

results = []
attacks = apply_attacks(watermarked)
for name, attacked in attacks:
    extracted = wm_sys.extract(attacked, original_shape)
    sim = calculate_similarity(watermark, extracted)
    results.append((name, sim, extracted))
    cv2.imwrite(f'output/attacked_{name}.jpg', attacked)
    cv2.imwrite(f'output/extracted_{name}.png', extracted)

# 打印结果
print("\n鲁棒性测试结果：")
print("-" * 40)
for name, sim, _ in results:
    print(f"{name:<15}: {sim:.2f}% 相似度")

# 可视化
plt.figure(figsize=(15, 10))
plt.subplot(2, 4, 1), plt.imshow(cv2.cvtColor(host, cv2.COLOR_BGR2RGB)), plt.title('原图'), plt.axis('off')
plt.subplot(2, 4, 2), plt.imshow(watermark, cmap='gray'), plt.title('原始水印'), plt.axis('off')
plt.subplot(2, 4, 3), plt.imshow(cv2.cvtColor(watermarked, cv2.COLOR_BGR2RGB)), plt.title('含水印图像'), plt.axis('off')
plt.subplot(2, 4, 4), plt.imshow(extracted_original, cmap='gray'), plt.title('提取水印'), plt.axis('off')

for i, (name, sim, wm) in enumerate(results[:4]):
    plt.subplot(2, 4, 5+i), plt.imshow(wm, cmap='gray')
    plt.title(f'{name}\n相似度: {sim:.1f}%'), plt.axis('off')

plt.tight_layout()
plt.savefig('output/watermark_results.png')
plt.show()
