from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .sample.ctseg import CTSegDataset


from .dataset.coco_seg import COCOSeg


dataset_factory = {
#  'coco': COCO,
#  'pascal': PascalVOC,
#  'kitti': KITTI,
#  'coco_hp': COCOHP,
  'coco_seg':COCOSeg,
}

_sample_factory = {
#  'exdet': EXDetDataset,
#  'ctdet': CTDetDataset,
#  'ddd': DddDataset,
#  'multi_pose': MultiPoseDataset,
  'ctseg':CTSegDataset,
}


def get_dataset(dataset, task):
  class Dataset(dataset_factory[dataset], _sample_factory[task]):
    pass
  return Dataset
  
