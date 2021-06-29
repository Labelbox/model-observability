from src.bounding_box import BBFormat, BoundingBox
from src.evaluators.coco_evaluator import get_coco_summary

from uuid import uuid4
import numpy as np
from typing import Any, Dict, Tuple, List

def create_mea_metric(metric_value, data_row_id) -> Dict[str, Any]:
    """ Create the upload format for mea metrics """
    return {
        "uuid" : str(uuid4()),
        "dataRow" : {
            "id": data_row_id,
        },
        "metricValue" : metric_value
    }

def format_bbox(bbox: Dict[str, int]):
    """Convert the bounding box from l,t,w,h to l,t,b,r"""
    return [
        bbox["left"],
        bbox["top"],
        bbox["left"] + bbox["width"],
        bbox["top"] + bbox["height"],
    ]

def swap_dims_and_scale(bbox :Tuple[float, float, float, float], image_h : int, image_w: int) -> Tuple[float, float, float, float]:
    """
    Convert normalized bbox with y0,x0,y1,x1 coordinates into image coordinates x0,y0,x1,y1
    """
    return [bbox[1] * image_w, bbox[0] * image_h, bbox[3] * image_w, bbox[2] * image_h]


def get_summary(preds : Dict[str, Any], gts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate summary statistics for a data row
    """
    result = get_coco_summary(gts, preds)
    result = {
        k: v
        for k, v in result.items()
        if k in ["AP", "AP50", "AP75", "AR1", "AR10", "AR100"] and not np.isnan(v)
    }
    scores = np.array([pred._confidence for pred in preds])
    for (fn, name) in [(np.mean, 'mean'), (np.max, 'max'), (np.min, 'min')]:
        value = 0. # set default so fn() doesn't raise value error if there were no predictions
        if len(scores):
            value = fn(scores)
        result[f'{name}_score'] = value
    result["predictions"] = len(preds)
    result["labels"] = len(gts)
    return result


def construct_boxes(inference : Dict[str, Any], annotation : Dict[str, Any], name="exp_name") -> Tuple[List[BoundingBox],List[BoundingBox]]:
    """
    Convert inference and annotation json payloads into a consistent BoundingBox format
    """
    annotation_boxes = [format_bbox(box) for box in annotation["boxes"]]
    image_size = (inference["image_w"], inference["image_h"])
    gt = [
        BoundingBox(
            name,
            class_id=class_name,
            coordinates=coords,
            format=BBFormat.XYX2Y2,
            img_size=image_size,
        )
        for coords, class_name in zip(annotation_boxes, annotation["class_names"])
    ]
    pred = [
        BoundingBox(
            name,
            class_id=class_name,
            coordinates=swap_dims_and_scale(coords, image_size[1], image_size[0]),
            img_size=image_size,
            format=BBFormat.XYX2Y2,
            confidence=score,
        )
        for coords, score, class_name in zip(
            inference["boxes"], inference["scores"], inference["class_names"]
        )
    ]
    return gt, pred


def format_annotation(json_label: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts the json representation of the label into a format that is easier to work with
    """
    instances = json_label["objects"]
    boxes = [annot["bbox"] for annot in instances]
    class_names = [annot["title"] for annot in instances]
    return {"boxes": boxes, "class_names": class_names}
