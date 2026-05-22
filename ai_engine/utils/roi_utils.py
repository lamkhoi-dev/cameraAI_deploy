"""ROI masking helpers for AI inference."""

from __future__ import annotations

from typing import Iterable

import cv2
import numpy as np


def apply_roi_mask(frame: np.ndarray, roi_polygon_points: Iterable[Iterable[float]] | None) -> np.ndarray:
    """Black out pixels outside the ROI polygon and return the masked frame."""
    if frame is None or roi_polygon_points is None:
        return frame

    points = np.array(list(roi_polygon_points), dtype=np.float32)
    if points.ndim != 2 or points.shape[0] < 3 or points.shape[1] < 2:
        return frame

    h, w = frame.shape[:2]
    polygon = np.round(points[:, :2]).astype(np.int32)
    polygon[:, 0] = np.clip(polygon[:, 0], 0, max(0, w - 1))
    polygon[:, 1] = np.clip(polygon[:, 1], 0, max(0, h - 1))

    if len(polygon) < 3:
        return frame

    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [polygon], 255)
    return cv2.bitwise_and(frame, frame, mask=mask)