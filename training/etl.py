#https://github.com/tensorflow/models/blob/master/research/object_detection/colab_tutorials/eager_few_shot_od_training_tf2_colab.ipynb

import os
from tqdm import tqdm
import requests
import random
import io
import numpy as np
from PIL import Image
from six import BytesIO
from multiprocessing.pool import ThreadPool as Pool
import tensorflow as tf
from labelbox import Client
from object_detection.utils import dataset_util
import config


def normalize_bbox(label, img_w, img_h):
    """
    - Reformat labelbox bounding box labels to kitti
    - Scales bbox coordinates to match the resizing applied to the image.
    """
    bbox = label['bbox']
    return [
        bbox['left'] / img_w,  # left
        bbox['top'] / img_h,  # top
        (bbox['left'] + bbox['width']) / img_w,  # right
        (bbox['top'] + bbox['height']) / img_h,  # bottom
    ]


def filter_labels(row):
    """
    Reads a sinlge label from a labelbox export and extracts only bounding box annotations
    """
    labels = [{
        'bbox': obj.get('bbox'),
        'name': obj.get('title')
    } for obj in row['Label'].get('objects', []) if (
        obj.get('bbox') is not None and obj.get('title') in config.class_names)]
    return labels


def partition_function(row, test_percentage=0.15):
    """
    If not using sequential data then the random partitioning is fine.
    """
    if random.random() < test_percentage:
        return 'test'
    else:
        return 'train'


def get_example(labels, orig_w, orig_h):
    examples = []
    for label in labels:
        class_name = label['name']
        normalized_box = normalize_bbox(label, orig_w, orig_h)
        examples.append({'name': class_name, 'bbox': normalized_box})
    return examples


def run_row(row):
    idx, row = row
    labels = filter_labels(row)
    if not len(labels):
        return
    image = row['Labeled Data']
    image_data = Image.open(BytesIO(requests.get(image).content))
    orig_w, orig_h = image_data.size
    image_data = image_data.resize((config.image_w, config.image_h))
    image_bytes = BytesIO()
    image_data.save(image_bytes, format="JPEG")
    labels = get_example(labels, orig_w, orig_h)
    dataset = partition_function(row)
    #TODO: Are these in the right order?
    xmins = [n['bbox'][0] for n in labels]
    ymins = [n['bbox'][1] for n in labels]
    xmaxs = [n['bbox'][2] for n in labels]
    ymaxs = [n['bbox'][3] for n in labels]

    tf_example = tf.train.Example(features=tf.train.Features(
        feature={
            'image':
                dataset_util.bytes_feature(image_bytes.getvalue()),
            'xmin':
                dataset_util.float_list_feature(xmins),
            'xmax':
                dataset_util.float_list_feature(xmaxs),
            'ymin':
                dataset_util.float_list_feature(ymins),
            'ymax':
                dataset_util.float_list_feature(ymaxs),
            'label':
                dataset_util.int64_list_feature(
                    [config.class_names.index(n['name']) for n in labels]),
        }))
    return tf_example, dataset


def write_records(records):
    writer_train = tf.io.TFRecordWriter(config.train_tfr_name)
    writer_test = tf.io.TFRecordWriter(config.test_tfr_name)
    writer_val = tf.io.TFRecordWriter(config.val_tfr_name)
    for record, dataset in records:
        if dataset == 'train':
            writer_train.write(record.SerializeToString())
        elif dataset == 'test':
            writer_test.write(record.SerializeToString())
        elif dataset == 'val':
            writer_val.write(record.SerializeToString())
        else:
            raise ValueError(f"Unexpected data... {dataset}")


if __name__ == '__main__':
    client = Client()
    project = client.get_project(config.labelbox_project_id)
    labels = project.export_labels()
    data = requests.get(labels).json()
    with Pool(12) as pool:
        records = list(
            tqdm(pool.imap(run_row, [[idx, r] for idx, r in enumerate(data)]),
                 total=len(data)))
    records = [r for r in records if r is not None]
    write_records(records)
