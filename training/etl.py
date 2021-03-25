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

from object_detection.utils import label_map_util
from object_detection.utils import config_util
from object_detection.builders import model_builder
from object_detection.utils import dataset_util

import json




IMAGE_H, IMAGE_W = 640, 640


class_names = ['animal'] # ,'human']
train_locations = [38, 43, 105]



def etl(examples):
    num_classes = len(class_mappings)
    category_indx = {}
    for idx, class_name in enumerate(class_names):
        category_index[class_name] = idx
    train_image_tensors = []
    gt_classes_one_hot_tensors = []
    gt_box_tensors = []
    for (train_image_np, gt_box_np) in examples:
        train_image_np = np.array(example['image'])
        gt_bbox_np = np.array(example['label']['bbox'])
        train_image_tensors.append(tf.expand_dims(tf.convert_to_tensor(train_image_np, dtype=tf.float32), axis=0))
        gt_box_tensors.append(tf.convert_to_tensor(gt_box_np, dtype=tf.float32))
        zero_indexed_groundtruth_classes = tf.convert_to_tensor([category_index[n] for n in example['label']['class_name']])
        gt_classes_one_hot_tensors.append(tf.one_hot(
                    zero_indexed_groundtruth_classes, num_classes))
    return train_image_tensors, gt_classes_one_hot_tensors, gt_box_tensors



def normalize_bbox(label, img_w, img_h):
    """
    - Reformat labelbox bounding box labels to kitti
    - Scales bbox coordinates to match the resizing applied to the image.
    """
    
    bbox = label['bbox']
    return [
            bbox['left'] / img_w,                    # left      
            bbox['top'] / img_h,                     # top
            (bbox['left'] + bbox['width']) / img_w,  # right
            (bbox['top'] + bbox['height']) / img_h,  # bottom            
        ]
              

def filter_labels(row):
    """
    Reads a sinlge label from a labelbox export and extracts only bounding box annotations
    """
    labels = [
        {
            'bbox' : obj.get('bbox'),
            'name' : obj.get('title')
        } 
        for obj in row['Label'].get('objects',[]) if (
            obj.get('bbox') is not None and obj.get('title') in class_names
        )
    ]
    return labels
    


def get_unique_locations(row, labels_path):
    if not hasattr(get_unique_locations, 'unique_locations'):        
        unique_locations = {json.load(open(os.path.join(labels_path,f)))['location'] for f in os.listdir(labels_path)}
        get_unique_locations.unique_locations = list(unique_locations)
    return get_unique_locations.unique_locations

    
def partition_sequential_data(row):
    """
    - The animal data comes from video frames 
        we don't want the train and test data to come from the same camera locations.
    """
    labels_path = 'labels'
    location_file = row['External ID'].split('/')[-1].replace('.jpg', '.json')    
    location = json.load(open(os.path.join(labels_path, location_file)))['location']
    #unique_locations = get_unique_locations(row, labels_path)
    #random.seed(1)
    #random.shuffle(unique_locations)
    #train_locations = unique_locations[:int(len(unique_locations)*0.8)]
    #test_locations = unique_locations[int(len(unique_locations)*0.2):]
    if location in train_locations:
        return "train"
    elif int(location) == 125:
        return "test"
    else:
        return "val"
        
def partition_function(row, test_percentage = 0.15):
    """
    If not using sequential data then the random partitioning is fine.
    """
    if 0: #USE_RANDOM_PARTITIONING:
        if random.random() < test_percentage:
            return 'test'
        else:
            return 'train'
    return partition_sequential_data(row)
        
def get_example(labels, orig_w, orig_h):
    examples = []
    for label in labels:
        class_name = label['name']
        normalized_box = normalize_bbox(label, orig_w, orig_h)
        examples.append( {'name' : class_name, 'bbox' : normalized_box} )
    return examples

    
def run_row(row):
    idx, row = row
    labels = filter_labels(row)
    if not len(labels):
        return
    image = row['Labeled Data']
    image_data = Image.open(BytesIO(requests.get(image).content))
    orig_w, orig_h = image_data.size
    image_data = image_data.resize((IMAGE_W, IMAGE_H))
    image_bytes = BytesIO()
    image_data.save(image_bytes, format = "JPEG")
    file_name = str(idx).zfill(5)
    labels = get_example(labels, orig_w, orig_h)
    dataset = partition_function(row)
    #TODO: Are these in the right order?
    xmins = [n['bbox'][0] for n in labels]
    ymins = [n['bbox'][1] for n in labels]
    xmaxs = [n['bbox'][2] for n in labels]
    ymaxs = [n['bbox'][3] for n in labels]

    tf_example = tf.train.Example(features=tf.train.Features(feature={
      'image': dataset_util.bytes_feature(image_bytes.getvalue()),
      'xmin': dataset_util.float_list_feature(xmins),
      'xmax': dataset_util.float_list_feature(xmaxs),
      'ymin': dataset_util.float_list_feature(ymins),
      'ymax': dataset_util.float_list_feature(ymaxs),
      'label': dataset_util.int64_list_feature([class_names.index(n['name']) for n in labels]),
    })) 
    return tf_example , dataset
        

if __name__ == '__main__':
    from labelbox import Client
    client = Client()
    LABELBOX_PROJECT_ID = "ckm4xyfncfgja0760vpfdxoro" 
    project = client.get_project(LABELBOX_PROJECT_ID)
    labels = project.export_labels()
    data = requests.get(labels).json()

    with Pool(12) as pool:
        records = list(tqdm(pool.imap(run_row, [[idx,r] for idx, r in enumerate(data)]), total = len(data)))
    records = [r for r in records if r is not None] 
    writer_train = tf.io.TFRecordWriter("/tmp/train_data.tfr")
    writer_test = tf.io.TFRecordWriter("/tmp/test_data.tfr")
    writer_val = tf.io.TFRecordWriter("/tmp/val_data.tfr")
    for record, dataset in records:
        if dataset == 'train':
            writer_train.write(record.SerializeToString())
        elif dataset == 'test':
            writer_test.write(record.SerializeToString())
        elif dataset == 'val':
            writer_val.write(record.SerializeToString())
        else:
            raise ValueError(f"Unexpected data... {dataset}")
 
        








