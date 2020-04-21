from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

#from .exdet import ExdetDetector
#from .ddd import DddDetector
#from .ctdet import CtdetDetector
#from .multi_pose import MultiPoseDetector
#from .multidet import MultiDetector
#from .sidev2 import SideV2Detector
from .ctseg import CtsegDetector

detector_factory = {
  'ctseg': CtsegDetector
  #'exdet': ExdetDetector, 
  #'ddd': DddDetector,
  #'ctdet': CtdetDetector,
  #'multi_pose': MultiPoseDetector, 
  #'bddet': CtdetDetector,
  #'sidedet': MultiPoseDetector,
  #'kitti3d': MultiPoseDetector,
  #'plusai': CtdetDetector,
  #'plusai_multicar': MultiDetector,
  #'plusai_3d': MultiPoseDetector,
  #'sidev2': SideV2Detector
}
