from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


class Sam2NotAvailable(Exception):
    pass


def _import_sam2():
    try:
        import torch  # noqa: F401
        from sam2.build_sam import build_sam2_video_predictor  # type: ignore
        return build_sam2_video_predictor
    except Exception as e:  # pragma: no cover
        raise Sam2NotAvailable(
            "SAM2 or its dependencies are not available in this environment."
        ) from e


def _device_from_torch():
    import torch

    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _sorted_frame_names(frames_dir: Path) -> List[str]:
    exts = {".png", ".jpg", ".jpeg"}
    names = [p.name for p in frames_dir.iterdir() if p.is_file() and p.suffix.lower() in exts]

    def key_fn(n: str) -> Tuple[int, str]:
        stem = Path(n).stem
        # Try to grab trailing digits (e.g., frame_0001 -> 1)
        digits = ""
        for ch in reversed(stem):
            if ch.isdigit():
                digits = ch + digits
            else:
                break
        num = int(digits) if digits else 0
        return (num, n)

    names.sort(key=key_fn)
    return names


def run_sam2_on_points(
    frames_dir: Path,
    coords: List[Tuple[float, float]],
    model_cfg: Path,
    checkpoint: Path,
    device_str: str | None = None,
) -> Dict[int, np.ndarray]:
    """
    Run SAM2 video propagation given a frames directory and two positive points on the first frame.

    Returns a dict: frame_idx -> binary mask (H, W) for obj_id=1.
    """
    build_predictor = _import_sam2()

    import torch

    if device_str:
        device = torch.device(device_str)
    else:
        device = _device_from_torch()

    predictor = build_predictor(str(model_cfg), str(checkpoint), device=device)

    # video_path accepts a directory of frames
    inference_state = predictor.init_state(video_path=str(frames_dir))
    predictor.reset_state(inference_state)

    # Frame index to annotate: first frame
    ann_frame_idx = 0
    points_np = np.array(coords, dtype=np.float32)
    labels_np = np.ones((len(coords),), dtype=np.int32)  # all positive

    obj_id = 1
    _, out_obj_ids, out_mask_logits = predictor.add_new_points_or_box(
        inference_state=inference_state,
        frame_idx=ann_frame_idx,
        obj_id=obj_id,
        box=None,
        points=points_np,
        labels=labels_np,
    )

    video_segments: Dict[int, np.ndarray] = {}
    for out_frame_idx, ids, mask_logits in predictor.propagate_in_video(inference_state):
        # Take the first object's mask logits (obj_id==1)
        for i, oid in enumerate(ids):
            if oid == obj_id:
                video_segments[out_frame_idx] = (mask_logits[i] > 0.0).cpu().numpy()
                break

    if 0 in video_segments:
        del video_segments[0]
    return video_segments



