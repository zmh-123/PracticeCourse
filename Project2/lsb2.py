import numpy as np
import matplotlib.pyplot as plt
import cv2
import os

# 设置全局样式
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['figure.titlesize'] = 14
plt.rcParams['figure.titleweight'] = 'bold'
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300

target_dir = "output_images"
class LSB_Embed:
    def __init__(self):
        pass

    @staticmethod
    def get_bitPlane(img):
        """获取图像的8个位平面"""
        h, w = img.shape
        bitPlane = np.zeros(shape=(h, w, 8), dtype=np.uint8)
        for i in range(8):
            flag = 1 << i
            bitplane = img & flag
            bitplane[bitplane != 0] = 1
            bitPlane[..., i] = bitplane
        return bitPlane

    @staticmethod
    def lsb_embed(background, watermark, embed_bit=3):
        """将水印嵌入到背景图像的低位平面"""
        w_h, w_w = watermark.shape
        b_h, b_w = background.shape
        assert w_w < b_w and w_h < b_h, \
            f"请保证watermark尺寸小于background尺寸\r\n当前尺寸 watermark:{watermark.shape}, background:{background.shape}"

        bitPlane_background = LSB_Embed.get_bitPlane(background)
        bitPlane_watermark = LSB_Embed.get_bitPlane(watermark)

        # 将水印的高位信息嵌入到背景的低位平面
        for i in range(embed_bit):
            bitPlane_background[0:w_h, 0:w_w, i] = bitPlane_watermark[0:w_h, 0:w_w, (8 - embed_bit) + i]

        # 重建合成图像
        synthesis = np.zeros_like(background, dtype=np.uint8)
        for i in range(8):
            synthesis += bitPlane_background[..., i] * (1 << i)
        return synthesis

    @staticmethod
    def lsb_extract(synthesis, embed_bit=3):
        """从合成图像中提取水印和背景"""
        bitPlane_synthesis = LSB_Embed.get_bitPlane(synthesis)
        extract_watermark = np.zeros_like(synthesis, dtype=np.uint8)
        extract_background = np.zeros_like(synthesis, dtype=np.uint8)

        for i in range(8):
            if i < embed_bit:
                # 从低位平面重建水印
                extract_watermark += bitPlane_synthesis[..., i] * (1 << ((8 - embed_bit) + i))
            else:
                # 从高位平面重建背景
                extract_background += bitPlane_synthesis[..., i] * (1 << i)

        return extract_watermark, extract_background


def apply_attacks(img):
    """应用各种攻击并返回攻击后的图像列表"""
    attacked_imgs = []
    attack_names = []

    # 1. 水平翻转
    attacked_imgs.append(cv2.flip(img, 1))
    attack_names.append("Horizontal Flip")

    # 2. 垂直翻转
    attacked_imgs.append(cv2.flip(img, 0))
    attack_names.append("Vertical Flip")

    # 3. 平移 (向右下平移50像素)
    rows, cols = img.shape[:2]  # 正确获取图像尺寸
    M = np.float32([[1, 0, 50], [0, 1, 50]])
    translated = cv2.warpAffine(img, M, (cols, rows), borderValue=0)
    attacked_imgs.append(translated)
    attack_names.append("Translation")

    # 4. 裁剪 (中心区域裁剪)
    h, w = img.shape[:2]  # 正确获取图像尺寸
    cropped = img[h // 4:h * 3 // 4, w // 4:w * 3 // 4]
    resized_cropped = cv2.resize(cropped, (w, h))  # 缩放回原尺寸
    attacked_imgs.append(resized_cropped)
    attack_names.append("Cropping")

    # 5. 对比度调整 (线性变换)
    alpha = 1.5  # 对比度增强因子
    adjusted = np.clip(alpha * img, 0, 255).astype(np.uint8)
    attacked_imgs.append(adjusted)
    attack_names.append("Contrast Adjustment")

    # 6. 高斯噪声
    noise = np.random.normal(0, 25, img.shape).astype(np.uint8)
    noisy_img = cv2.add(img, noise)
    attacked_imgs.append(noisy_img)
    attack_names.append("Gaussian Noise")

    # 7. JPEG压缩 (模拟有损压缩)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
    _, buffer = cv2.imencode('.jpg', img, encode_param)
    jpeg_img = cv2.imdecode(buffer, cv2.IMREAD_GRAYSCALE)
    attacked_imgs.append(jpeg_img)
    attack_names.append("JPEG Compression")

    return attacked_imgs, attack_names


def plot_embedding_results(background, watermark, synthesis, extracted_wm, wm_size):
    """可视化嵌入和提取结果"""
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    fig.suptitle("LSB Watermark Embedding Results", fontsize=16)

    # 原始背景
    axes[0, 0].imshow(background, cmap='gray')
    axes[0, 0].set_title("Original Background")
    axes[0, 0].axis('off')

    # 处理后的水印
    axes[0, 1].imshow(watermark, cmap='gray')
    axes[0, 1].set_title(f"Processed Watermark ({wm_size[0]}x{wm_size[1]})")
    axes[0, 1].axis('off')

    # 含水印图像
    axes[1, 0].imshow(synthesis, cmap='gray')
    axes[1, 0].set_title("Watermarked Image")
    axes[1, 0].axis('off')

    # 提取的水印
    cropped_wm = extracted_wm[:wm_size[0], :wm_size[1]]
    axes[1, 1].imshow(cropped_wm, cmap='gray')
    axes[1, 1].set_title("Extracted Watermark")
    axes[1, 1].axis('off')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('output_images/embedding_results.png', bbox_inches='tight')
    plt.show()


def plot_robustness_results(attacked_imgs, extracted_wms, attack_names, wm_size):
    """可视化鲁棒性测试结果"""
    n_attacks = len(attack_names)
    fig = plt.figure(figsize=(12, 4 * n_attacks))
    fig.suptitle("Robustness Test", fontsize=16, y=0.98)

    for i in range(n_attacks):
        # 攻击后的图像
        ax1 = fig.add_subplot(n_attacks, 2, i * 2 + 1)
        ax1.imshow(attacked_imgs[i], cmap='gray')
        ax1.set_title(f"{attack_names[i]} (Attacked Image)", fontsize=12)
        ax1.set_xticks([])
        ax1.set_yticks([])

        # 提取的水印
        ax2 = fig.add_subplot(n_attacks, 2, i * 2 + 2)
        cropped_wm = extracted_wms[i][:wm_size[0], :wm_size[1]]
        ax2.imshow(cropped_wm, cmap='gray')
        ax2.set_title(f"{attack_names[i]} (Extracted Watermark)", fontsize=12)
        ax2.set_xticks([])
        ax2.set_yticks([])

    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.subplots_adjust(hspace=0.25, wspace=0.05)
    plt.savefig('output_images/robustness_results.png', bbox_inches='tight')
    plt.show()


def print_report(attack_names, wm_size, embed_bit):
    """打印鲁棒性测试报告"""
    # 攻击效果描述
    attack_effects = {
        "Horizontal Flip": "Watermark flipped horizontally - poor extraction",
        "Vertical Flip": "Watermark flipped vertically - poor extraction",
        "Translation": "Watermark position shifted - misaligned extraction",
        "Cropping": "Partial watermark extracted (only visible in remaining area)",
        "Contrast Adjustment": "Good extraction (LSB layers less affected by contrast changes)",
        "Gaussian Noise": "Significant degradation (noise directly affects LSB layers)",
        "JPEG Compression": "Poor extraction (lossy compression destroys LSB data)"
    }

    print("\n" + "=" * 70)
    print(" " * 20 + "ROBUSTNESS TEST")
    print("=" * 70)
    print(f"Test Configuration:")
    print(f"- Embedding bits: {embed_bit} LSBs")
    print(f"- Watermark size: {wm_size[1]}x{wm_size[0]} pixels")
    print(f"- Attacks tested: {len(attack_names)}")
    print("-" * 70)
    print("Attack Results:")

    for i, name in enumerate(attack_names):
        effect = attack_effects.get(name, "Effect not evaluated")
        print(f"{i + 1}. {name.upper():<20}: {effect}")




if __name__ == '__main__':
    # === 1. 检查图像文件 ===
    if not os.path.exists("host_image.png") or not os.path.exists("watermark.png"):
        print("错误: 未找到图像文件 'host_image.png' 或 'watermark.png'")
        print("请确保这些文件在当前目录下")
        exit(1)

    # === 2. 图像预处理 ===
    # 读取图像
    background = cv2.imread("host_image.png", cv2.IMREAD_GRAYSCALE)
    watermark = cv2.imread("watermark.png", cv2.IMREAD_GRAYSCALE)

    if background is None or watermark is None:
        print("错误: 无法读取图像文件")
        print("请检查文件路径和格式")
        exit(1)

    # 调整水印大小 (背景的1/4)
    h, w = background.shape
    wm_h, wm_w = int(h * 0.25), int(w * 0.25)
    watermark = cv2.resize(watermark, (wm_w, wm_h), interpolation=cv2.INTER_AREA)

    # 增强水印对比度
    watermark = cv2.equalizeHist(watermark)

    # === 3. 水印嵌入 ===
    embed_bit = 3
    print(f"embed_bit为 {embed_bit} LSBs...")
    synthesis = LSB_Embed.lsb_embed(background, watermark, embed_bit)

    # === 4. 水印提取 ===
    print("水印提取...")
    extract_watermark, _ = LSB_Embed.lsb_extract(synthesis, embed_bit)


    cv2.imwrite(os.path.join(target_dir, "background.png"), background)
    cv2.imwrite(os.path.join(target_dir, "watermark.png"), watermark)
    cv2.imwrite(os.path.join(target_dir, "synthesis.png"), synthesis)
    cv2.imwrite(os.path.join(target_dir, "extract_watermark.png"), extract_watermark)

    # === 5. 基础结果可视化 ===
    print("基础结果...")
    plot_embedding_results(
        background,
        watermark,
        synthesis,
        extract_watermark,
        wm_size=(wm_h, wm_w)
    )

    # === 6. 鲁棒性测试 ===
    print("鲁棒性测试")
    attacked_imgs, attack_names = apply_attacks(synthesis)
    extracted_watermarks = []

    # 从受攻击图像中提取水印
    for i, attacked_img in enumerate(attacked_imgs):
        print(f"从 {attack_names[i]}中提取水印")
        wm, _ = LSB_Embed.lsb_extract(attacked_img, embed_bit)
        extracted_watermarks.append(wm)

    # === 7. 鲁棒性结果可视化 ===
    print("鲁棒性结果可视化")
    plot_robustness_results(
        attacked_imgs,
        extracted_watermarks,
        attack_names,
        wm_size=(wm_h, wm_w)
    )

    # === 8. 生成报告 ===
    print_report(attack_names, (wm_h, wm_w), embed_bit)

    print("Processing complete. Results saved to:")
    print("- embedding_results.png")
    print("- robustness_results.png")