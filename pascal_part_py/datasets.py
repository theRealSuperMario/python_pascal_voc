import os
import numpy as np
import glob

from pascal_part_py.pascal_part_annotation import ImageAnnotation

import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt

from pascal_part_py import voc_utils
import functools
import cv2


class PascalVOCDataset:
    def __init__(self, dir_VOC_root, object_class, data_split):
        """Dataset class for PASCAL VOC 20xx. 
        Iterates over single images. Annotations contain bounding boxes for objects in the image. 
        There can be multiple objects in an image, therefore annotations may contain multiple object annotations.

        For instance, Pascal VOC2010 train set contains 4998 images, thus the length of this dataset is 4998

        See examples and demo for further usage.
        
        Parameters
        ----------
        dir_VOC_root : str
            path to VOC root, i.e. 'xxx/VOCdevkit/VOC20xx'.
        object_class : OBJECT_CLASS or None
            object class to use. If `None`, will use entire data split.
        data_split : DATA_SPLIT
            data split to use, i.e. "train", "val", "trainval"


        Examples
        --------

            # Load only aeroplane class from train split
            dset = voc_utils.PascalVOCDataset(
                DIR_VOC_ROOT, voc_utils.OBJECT_CLASS.aeroplane, voc_utils.DATA_SPLIT.train
            )
            assert len(dset) == 283  # pascal VOC 2010

            # load entire train set
            dset = voc_utils.PascalVOCDataset(
                DIR_VOC_ROOT, None, voc_utils.DATA_SPLIT.train
            )
            assert len(dset) == 4998  # pascal VOC 2010

        """
        self.voc = voc_utils.VOCLoader(dir_VOC_root)
        self.image_set = voc_utils.get_image_set(object_class, data_split)
        self.files = self.voc.load_image_set_as_list(self.image_set)

    def __len__(self):
        return len(self.files)

    def __getitem__(self, i):
        fname = self.files[i]
        annotation_file = self.voc.get_annotationpath_from_fname(fname)
        annotation = self.voc.load_annotation(annotation_file)

        image_file = self.voc.get_jpegpath_from_fname(fname)
        image = cv2.imread(image_file)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        example = annotation
        example["image"] = image
        return example


class CroppedPascalVOCDataset:
    def __init__(self, dir_VOC_root, dir_cropped_csv, object_class, data_split):
        """Dataset class for iterating over every single annotated object box in the Pascal dataset.
        
        In the Pascal dataset, annotations per image can contain multiple object bounding boxes.
        If you want to crop every object out of the image and iterate over those crops, use this class.

        For instance, Pascal VOC2010 train set contains 4998 images, but 13339 annotated objects. 
        Thus the length of this dataset is 13339.

        You can filter by `object_class` and data split.

        
        To prevent figuring out the object boxes every time this class is instantiated,
        the data is stored in separate csv files in `dir_cropped_csv` and reloaded.
        I recommend NOT setting `dir_cropped_csv` to a subdir within the vOC dataset, but 
        to some other path.

        
        Parameters
        ----------
        dir_VOC_root : str
            path to VOC root, i.e. 'xxx/VOCdevkit/VOC20xx'.
        dir_cropped_csv : str
            path to directory where to store intermediate csv files. Preferrably NOT within VOC subdirectory.
        object_class : OBJECT_CLASS or None
            object class to use. If `None`, will use entire data split.
        data_split : DATA_SPLIT
            data split to use, i.e. "train", "val", "trainval"

        Examples
        --------

            csv_dir = tmpdir.mkdir("csv")
            dset = voc_utils.CroppedPascalVOC(
                DIR_VOC_ROOT,
                csv_dir,
                voc_utils.OBJECT_CLASS.aeroplane,
                voc_utils.DATA_SPLIT.train,
            )
            ex = dset[0]
            assert len(dset) == 403  # pascal VOC 2010
        """
        self.voc = voc_utils.VOCLoader(dir_VOC_root)
        self.dir_cropped_csv = dir_cropped_csv
        self.files = self.voc.load_object_class_cropped_as_list(
            object_class, data_split, dir_cropped_csv
        )
        # files is a list of {"fname" : xxx.jpg, "xmin" : xmin, "ymin" : ymin, ...}

    def __len__(self):
        return len(self.files)

    def __getitem__(self, i):
        example = self.files[i]
        fname = example["fname"]
        image_file = self.voc.get_jpegpath_from_fname(fname)
        image = cv2.imread(image_file)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        bbox = {
            "xmin": int(example["xmin"]),
            "xmax": int(example["xmax"]),
            "ymin": int(example["ymin"]),
            "ymax": int(example["ymax"]),
        }
        crop = functools.partial(voc_utils.crop_box, **bbox)
        example["image"] = crop(image)
        return example


class PascalPartDataset(PascalVOCDataset):
    def __init__(
        self, VOC_root_dir, dir_Annotations_Part, object_class, data_split,
    ):
        """Dataset to iterate over Pascal Parts Dataset
        
        Parameters
        ----------
        VOC_root_dir : str
            directory from VOC 2010 or later dataset, subdirs `JPEGImages`, `Annotations`, `ImageSets/Main`
        dir_Annotations_Part : str
            directory `Annotations_Part` from pascal parts dataset, contains .mat files
        """
        self.dir_Annotations_Part = dir_Annotations_Part
        super(PascalPartDataset, self).__init__(VOC_root_dir, object_class, data_split)

    def __getitem__(self, i):
        example = super(PascalPartDataset, self).__getitem__(i)
        fname = example["annotation"]["filename"]  # .jpg file
        fname = os.path.splitext(fname)[0]
        fname_im = fname + ".jpg"
        fname_part_anno = fname + ".mat"
        an = ImageAnnotation(
            os.path.join(self.voc.dir_JPEGImages, fname_im),
            os.path.join(self.dir_Annotations_Part, fname_part_anno),
        )
        return {
            "annotations_part": an,
            "image": an.im,
            "class_segmentation": an.cls_mask,
            "instance_segmentation": an.inst_mask,
            "part_segmentation": an.part_mask,
            "annotation": example["annotation"],
        }


class CroppedPascalPartDataset(CroppedPascalVOCDataset):
    def __init__(
        self,
        VOC_root_dir,
        dir_cropped_csv,
        dir_Annotations_Part,
        object_class,
        data_split,
    ):
        self.dir_Annotations_Part = dir_Annotations_Part
        super(CroppedPascalPartDataset, self).__init__(
            VOC_root_dir, dir_cropped_csv, object_class, data_split
        )

    def __getitem__(self, i):
        example = super(CroppedPascalPartDataset, self).__getitem__(i)
        fname = example["fname"]
        fname_im = fname + ".jpg"
        fname_part_anno = fname + ".mat"
        an = ImageAnnotation(
            os.path.join(self.voc.dir_JPEGImages, fname_im),
            os.path.join(self.dir_Annotations_Part, fname_part_anno),
        )
        bbox = {
            "xmin": int(example["xmin"]),
            "xmax": int(example["xmax"]),
            "ymin": int(example["ymin"]),
            "ymax": int(example["ymax"]),
        }
        crop = functools.partial(voc_utils.crop_box, **bbox)
        example["image"] = crop(an.im)
        example["class_segmentation"] = crop(an.cls_mask)
        example["instance_segmentation"] = crop(an.inst_mask)
        example["part_segmentation"] = crop(an.part_mask)
        return example

