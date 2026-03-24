import base64
import os
from typing import Any, Dict

import cv2
import numpy as np
from langchain.tools import tool
from langchain_core.tools import ToolException

THRESHOLD_PROFILES: Dict[str, Dict[str, float]] = {
    # 保守档：更偏向避免误报，只有在证据很强时才判为差异
    "conservative": {
        # ssim_threshold: 结构相似度阈值，越高表示“同一场景”判定越严格
        "ssim_threshold": 0.80,
        # min_good_feature_matches: 最小有效特征匹配点数量，越高越严格
        "min_good_feature_matches": 60.0,
        # min_feature_inlier_ratio: RANSAC内点比例下限，越高越严格
        "min_feature_inlier_ratio": 0.40,
        # min_feature_match_quality: 特征综合质量下限，越高越严格
        "min_feature_match_quality": 0.30,
        # high_diff_ssim_threshold: 低于该SSIM且特征质量也低时，判为高差异
        "high_diff_ssim_threshold": 0.50,
        # high_diff_match_quality_threshold: 与high_diff_ssim_threshold配合判“高差异”
        "high_diff_match_quality_threshold": 0.15,
    },
    # 标准档：通用默认档位，适合大多数监控场景
    "standard": {
        "ssim_threshold": 0.72,
        "min_good_feature_matches": 25.0,
        "min_feature_inlier_ratio": 0.25,
        "min_feature_match_quality": 0.16,
        "high_diff_ssim_threshold": 0.45,
        "high_diff_match_quality_threshold": 0.10,
    },
    # 敏感档：更容易判为“无差异”，用于尽量减少误报
    "sensitive": {
        "ssim_threshold": 0.65,
        "min_good_feature_matches": 12.0,
        "min_feature_inlier_ratio": 0.20,
        "min_feature_match_quality": 0.12,
        "high_diff_ssim_threshold": 0.40,
        "high_diff_match_quality_threshold": 0.08,
    },
    # 激进档：用于仓库异常检测，倾向更早识别差异（误报率可能上升）
    "aggressive": {
        "ssim_threshold": 0.86,
        "min_good_feature_matches": 160.0,
        "min_feature_inlier_ratio": 0.80,
        "min_feature_match_quality": 0.85,
        "high_diff_ssim_threshold": 0.58,
        "high_diff_match_quality_threshold": 0.25,
    },
    # 超激进档：夜间、遮挡、轻微移位也希望触发报警，误报率会进一步上升
    "aggressive_plus": {
        "ssim_threshold": 0.90,
        "min_good_feature_matches": 220.0,
        "min_feature_inlier_ratio": 0.88,
        "min_feature_match_quality": 0.90,
        "high_diff_ssim_threshold": 0.62,
        "high_diff_match_quality_threshold": 0.30,
    },
}


def _decode_image(image_source: str) -> np.ndarray:
    """将输入解析为OpenCV图像，支持本地路径与base64字符串。"""
    if os.path.exists(image_source):
        image = cv2.imread(image_source)
        if image is None:
            raise ToolException(f"无法读取图片文件: {image_source}")
        return image
    try:
        payload = image_source.split(",", 1)[1] if "," in image_source else image_source
        raw = base64.b64decode(payload, validate=True)
        buf = np.frombuffer(raw, dtype=np.uint8)
        image = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if image is None:
            raise ToolException("base64内容不是有效图片")
        return image
    except Exception as exc:
        raise ToolException(f"图片解码失败，请传入有效文件路径或base64: {exc}") from exc


def _preprocess_gray(image: np.ndarray, width: int, height: int) -> np.ndarray:
    """统一尺寸并进行灰度增强，降低昼夜/红外差异对比对结果的干扰。"""
    resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return cv2.GaussianBlur(enhanced, (3, 3), 0)


def _compute_ssim(gray_a: np.ndarray, gray_b: np.ndarray) -> float:
    """计算结构相似度SSIM，结果范围通常在[0, 1]，越高表示结构越相似。"""
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    x = gray_a.astype(np.float64)
    y = gray_b.astype(np.float64)
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.T)
    mu_x = cv2.filter2D(x, -1, window)[5:-5, 5:-5]
    mu_y = cv2.filter2D(y, -1, window)[5:-5, 5:-5]
    mu_x2 = mu_x * mu_x
    mu_y2 = mu_y * mu_y
    mu_xy = mu_x * mu_y
    sigma_x2 = cv2.filter2D(x * x, -1, window)[5:-5, 5:-5] - mu_x2
    sigma_y2 = cv2.filter2D(y * y, -1, window)[5:-5, 5:-5] - mu_y2
    sigma_xy = cv2.filter2D(x * y, -1, window)[5:-5, 5:-5] - mu_xy
    denom = (mu_x2 + mu_y2 + c1) * (sigma_x2 + sigma_y2 + c2)
    denom = np.where(denom == 0, 1e-12, denom)
    ssim_map = ((2 * mu_xy + c1) * (2 * sigma_xy + c2)) / denom
    return float(np.mean(ssim_map))


def _feature_matching(gray_a: np.ndarray, gray_b: np.ndarray) -> Dict[str, float]:
    """基于ORB+KNN+RANSAC计算特征匹配质量。"""
    orb = cv2.ORB_create(nfeatures=1200, scaleFactor=1.2, nlevels=8)
    kp_a, des_a = orb.detectAndCompute(gray_a, None)
    kp_b, des_b = orb.detectAndCompute(gray_b, None)
    if des_a is None or des_b is None or len(kp_a) == 0 or len(kp_b) == 0:
        return {
            "keypoints_a": float(len(kp_a) if kp_a is not None else 0),
            "keypoints_b": float(len(kp_b) if kp_b is not None else 0),
            "good_matches": 0.0,
            "inlier_ratio": 0.0,
            "match_quality": 0.0,
        }
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    knn_matches = matcher.knnMatch(des_a, des_b, k=2)
    good_matches = []
    for pair in knn_matches:
        if len(pair) < 2:
            continue
        m, n = pair
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)
    if not good_matches:
        return {
            "keypoints_a": float(len(kp_a)),
            "keypoints_b": float(len(kp_b)),
            "good_matches": 0.0,
            "inlier_ratio": 0.0,
            "match_quality": 0.0,
        }
    inlier_ratio = 0.0
    if len(good_matches) >= 8:
        src = np.float32([kp_a[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst = np.float32([kp_b[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        _, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
        if mask is not None:
            inlier_ratio = float(mask.ravel().sum() / len(good_matches))
    coverage = min(1.0, len(good_matches) / 180.0)
    quality = 0.65 * coverage + 0.35 * inlier_ratio
    return {
        "keypoints_a": float(len(kp_a)),
        "keypoints_b": float(len(kp_b)),
        "good_matches": float(len(good_matches)),
        "inlier_ratio": float(inlier_ratio),
        "match_quality": float(quality),
    }


@tool(
    "opencv_image_compare_tool",
    description="OpenCV图片对比工具，支持文件路径和base64输入，融合SSIM与特征点匹配做差异判断.",
)
def opencv_image_compare_tool(image1_source: str, image2_source: str) -> Dict[str, Any]:
    """
    OpenCV图片对比工具，支持文件路径和base64输入，融合SSIM与特征点匹配做差异判断。

    参数说明:
        image1_source: 基准图，支持本地文件路径或base64。
        image2_source: 对比图，支持本地文件路径或base64。
        profile: 阈值档位，可选conservative/standard/sensitive/aggressive/aggressive_plus，默认standard。

    返回参数说明:
        是否存在显著差异: 是/否。
        差异等级: 高/中/低/低（疑似昼夜或红外差异）。
        判断依据: 中文说明，包含结构相似度与特征匹配两类依据。
        结论: 中文结论摘要。
        使用档位: 当前阈值档位。
    """
    # 当前固定使用aggressive档位进行仓库异常检测，如需更高敏可改为aggressive_plus
    profile = "aggressive"
    normalized_profile = profile.strip().lower()
    if normalized_profile not in THRESHOLD_PROFILES:
        raise ToolException(
            f"无效档位: {profile}，可选档位为 {list(THRESHOLD_PROFILES.keys())}"
        )
    selected_thresholds = THRESHOLD_PROFILES[normalized_profile]
    ssim_threshold = float(selected_thresholds["ssim_threshold"])
    min_good_feature_matches = int(selected_thresholds["min_good_feature_matches"])
    min_feature_inlier_ratio = float(selected_thresholds["min_feature_inlier_ratio"])
    min_feature_match_quality = float(selected_thresholds["min_feature_match_quality"])
    high_diff_ssim_threshold = float(selected_thresholds["high_diff_ssim_threshold"])
    high_diff_match_quality_threshold = float(
        selected_thresholds["high_diff_match_quality_threshold"]
    )

    image1 = _decode_image(image1_source)
    image2 = _decode_image(image2_source)
    h = min(image1.shape[0], image2.shape[0], 900)
    w = min(image1.shape[1], image2.shape[1], 1600)
    gray1 = _preprocess_gray(image1, w, h)
    gray2 = _preprocess_gray(image2, w, h)

    ssim_score = _compute_ssim(gray1, gray2)
    feature_stats = _feature_matching(gray1, gray2)

    feature_ok = (
        feature_stats["good_matches"] >= min_good_feature_matches
        and feature_stats["inlier_ratio"] >= min_feature_inlier_ratio
        and feature_stats["match_quality"] >= min_feature_match_quality
    )
    structural_ok = ssim_score >= ssim_threshold
    significant_difference = not (structural_ok or feature_ok)

    if significant_difference:
        if (
            ssim_score < high_diff_ssim_threshold
            and feature_stats["match_quality"] < high_diff_match_quality_threshold
        ):
            diff_level = "high"
        else:
            diff_level = "medium"
        summary = "检测到显著差异，建议人工复核现场变化。"
    else:
        if not structural_ok and feature_ok:
            diff_level = "low_lighting_or_infrared_shift"
            summary = "整体结构可能受昼夜/红外成像影响，但特征点匹配显示场景主体一致。"
        else:
            diff_level = "low"
            summary = "未检测到显著差异。"
    ssim_basis = f"结构相似度SSIM={ssim_score:.4f}，阈值={ssim_threshold:.4f}"
    feature_basis = (
        f"特征匹配数={int(feature_stats['good_matches'])}(阈值={min_good_feature_matches})，"
        f"内点比例={feature_stats['inlier_ratio']:.4f}(阈值={min_feature_inlier_ratio:.4f})，"
        f"特征质量={feature_stats['match_quality']:.4f}(阈值={min_feature_match_quality:.4f})"
    )
    rule_basis = "判定规则：结构通过或特征通过则判定无显著差异；结构与特征均不通过则判定存在显著差异。"
    basis_text = f"{ssim_basis}；{feature_basis}。{rule_basis}"
    return {
        "是否存在显著差异": "是" if significant_difference else "否",
        "差异等级": (
            "高"
            if diff_level == "high"
            else (
                "中"
                if diff_level == "medium"
                else (
                    "低（疑似昼夜或红外差异）"
                    if diff_level == "low_lighting_or_infrared_shift"
                    else "低"
                )
            )
        ),
        "判断依据": basis_text,
        "结论": summary,
        "使用档位": normalized_profile,
    }
