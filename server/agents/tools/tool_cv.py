import cv2
import numpy as np
import base64
import os
import requests
from typing import Optional, Union, Tuple, Dict, Any
from langchain.tools import tool
from langchain_core.tools import ToolException

def _decode_image(image_source: str) -> np.ndarray:
    """
    从文件路径或 base64 字符串解码图像。
    """
    try:
        # 检查是否为文件路径
        if os.path.exists(image_source):
            img = cv2.imread(image_source)
            if img is None:
                raise ValueError(f"Could not read image from path: {image_source}")
            return img
        
        # 检查是否为 URL
        if image_source.startswith(('http://', 'https://')):
            resp = requests.get(image_source, stream=True)
            resp.raise_for_status()
            arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
            img = cv2.imdecode(arr, -1)
            if img is None:
                raise ValueError(f"Could not decode image from URL: {image_source}")
            return img

        # 默认按 base64 处理
        # 若存在头信息则移除（例如 "data:image/jpeg;base64,"）
        if "," in image_source:
            image_source = image_source.split(",")[1]
        
        image_data = base64.b64decode(image_source)
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Could not decode base64 image")
            
        return img
    except Exception as e:
        raise ToolException(f"Error loading image: {str(e)}")

def _preprocess_image(img: np.ndarray, target_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
    """
    转为灰度并应用 CLAHE，以增强对光照变化的不变性。
    如果提供 target_size，则进行缩放。
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    if target_size:
        gray = cv2.resize(gray, target_size)
    
    # 应用 CLAHE（限制对比度的自适应直方图均衡化）
    # 这有助于处理昼夜或红外/可见光差异
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    return enhanced

def _compute_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    计算两张灰度图之间的结构相似性指数（SSIM）。
    实现参考 Wang 等人（2004）。
    """
    C1 = (0.01 * 255)**2
    C2 = (0.03 * 255)**2

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.transpose())

    mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]  # 有效区域模式（valid mode）
    mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]
    
    mu1_sq = mu1**2
    mu2_sq = mu2**2
    mu1_mu2 = mu1 * mu2
    
    sigma1_sq = cv2.filter2D(img1**2, -1, window)[5:-5, 5:-5] - mu1_sq
    sigma2_sq = cv2.filter2D(img2**2, -1, window)[5:-5, 5:-5] - mu2_sq
    sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
               ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
               
    return ssim_map.mean()

def _feature_matching(img1: np.ndarray, img2: np.ndarray) -> Dict[str, Any]:
    """
    使用 ORB 检测并匹配特征点。
    """
    # 初始化 ORB 检测器
    orb = cv2.ORB_create(nfeatures=500)
    
    # 提取关键点与描述子
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    
    if des1 is None or des2 is None:
        return {"matches": 0, "score": 0.0, "status": "no_features"}
        
    # 创建 BFMatcher 对象
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
    # 匹配描述子
    matches = bf.match(des1, des2)
    
    # 按距离从小到大排序
    matches = sorted(matches, key=lambda x: x.distance)
    
    # 根据匹配数量和平均距离计算分数
    # 距离越小越好，匹配数量越多越好。
    num_matches = len(matches)
    if num_matches == 0:
        return {"matches": 0, "score": 0.0}
        
    avg_distance = sum(m.distance for m in matches) / num_matches
    
    # 归一化分数（启发式）：
    # 完美匹配距离为 0。
    # 对 ORB（Hamming）而言，距离上限可近似视为 ~100。
    # 目标分数范围为 0-1。
    match_quality = max(0, 1 - (avg_distance / 64.0)) # 64 是“较好匹配”的启发式最大距离
    
    return {
        "matches": num_matches,
        "avg_distance": avg_distance,
        "match_quality": match_quality
    }

@tool
def image_comparison_tool(image1_source: str, image2_source: str) -> Dict[str, Any]:
    """
    使用 OpenCV 比较两张图像，检测差异、结构相似度和特征匹配情况。
    对光照变化（昼夜、红外）具有较好鲁棒性。
    
    参数:
        image1_source: 第一张图像的文件路径或 base64 字符串。
        image2_source: 第二张图像的文件路径或 base64 字符串。
        
    返回:
        一个字典，包含：
        - ssim_score: 结构相似性指数（0 到 1，越高越相似）。
        - feature_match_score: 基于特征匹配的分数（0 到 1）。
        - significant_difference: 布尔值，表示图像是否存在显著差异。
        - description: 对比结果的文本描述。
    """
    try:
        # 1. 加载图像
        img1 = _decode_image(image1_source)
        img2 = _decode_image(image2_source)
        
        # 2. 缩放到较小尺寸以便比较
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        target_h, target_w = min(h1, h2), min(w1, w2)
        
        # 预处理（灰度 + CLAHE）
        processed_img1 = _preprocess_image(img1, (target_w, target_h))
        processed_img2 = _preprocess_image(img2, (target_w, target_h))
        
        # 3. 计算 SSIM
        ssim_score = _compute_ssim(processed_img1, processed_img2)
        
        # 4. 特征匹配
        # 特征匹配可使用原始分辨率（灰度/增强后）以捕捉更多细节，也可使用缩放后图像。
        # 这里为保持一致性，使用预处理后的图像。
        feature_stats = _feature_matching(processed_img1, processed_img2)
        
        # 5. 结果分析
        # 阈值（启发式）
        SSIM_THRESHOLD = 0.85  # 低于该值，结构差异显著
        MATCH_QUALITY_THRESHOLD = 0.4 # 低于该值，特征匹配较差
        HIGH_MATCH_QUALITY_THRESHOLD = 0.5 # 若匹配质量达到该值，在光照变化场景下优先参考特征匹配
        
        is_different = False
        reasons = []
        diff_level = "Low"
        
        if ssim_score < SSIM_THRESHOLD:
            reasons.append(f"Low structural similarity ({ssim_score:.2f})")
            # 检查特征匹配是否能“纠偏”（例如白天 vs 夜晚）
            if feature_stats["match_quality"] > HIGH_MATCH_QUALITY_THRESHOLD:
                is_different = False
                reasons.append("but high feature match indicates same scene with different conditions (e.g., lighting)")
                diff_level = "Low (Lighting/Condition Change)"
            else:
                is_different = True
                diff_level = "High" if ssim_score < 0.6 else "Moderate"
        else:
            is_different = False
            
        if feature_stats["match_quality"] < MATCH_QUALITY_THRESHOLD and ssim_score >= SSIM_THRESHOLD:
             # SSIM 高但特征匹配低？不常见，但在纹理较少时可能出现。
             # 这种情况下通常优先相信 SSIM。
             pass

        result = {
            "ssim_score": float(ssim_score),
            "feature_matches": feature_stats["matches"],
            "feature_match_quality": float(feature_stats["match_quality"]),
            "significant_difference": is_different,
            "difference_level": diff_level,
            "details": ", ".join(reasons) if reasons else "Images are similar"
        }
        
        return result

    except Exception as e:
        return {"error": str(e)}
