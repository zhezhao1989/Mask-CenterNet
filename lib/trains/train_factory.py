from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

#from .ctdet import CtdetTrainer
#from .ddd import DddTrainer
#from .exdet import ExdetTrainer
#from .multi_pose import MultiPoseTrainer
#from .multi_car import MultiCarTrainer
#from .sidev2 import SideV2Trainer
from .ctseg import CtsegTrainer

train_factory = {
#  'exdet': ExdetTrainer, 
#  'ddd': DddTrainer,
#  'ctdet': CtdetTrainer,
#  'multi_pose': MultiPoseTrainer, 
#  'bddet': CtdetTrainer,
#  'sidedet': MultiPoseTrainer,
#  'kitti3d': MultiPoseTrainer,
#  'plusai': CtdetTrainer,
#  'plusai_multicar': MultiCarTrainer,
#  'plusai_wi': CtdetTrainer,
#  'plusai_3d': MultiPoseTrainer,
#  'sidev2': SideV2Trainer
   'ctseg': CtsegTrainer
}

