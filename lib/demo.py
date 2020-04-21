from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import _init_paths

import os
import cv2
import json

from opts import opts
from detectors.detector_factory import detector_factory

image_ext = ['jpg', 'jpeg', 'png', 'webp']
video_ext = ['mp4', 'mov', 'avi', 'mkv']
time_stats = ['tot', 'load', 'pre', 'net', 'dec', 'post', 'merge']
cls_name = ['bike','bus','car','motor','person','rider','traffic light','traffic sign','train','truck']

def demo(opt):
  os.environ['CUDA_VISIBLE_DEVICES'] = opt.gpus_str
  #opt.debug = max(opt.debug, 1)
  Detector = detector_factory[opt.task]
  detector = Detector(opt)

  if opt.demo == 'webcam' or \
    opt.demo[opt.demo.rfind('.') + 1:].lower() in video_ext:
    cam = cv2.VideoCapture(0 if opt.demo == 'webcam' else opt.demo)
    detector.pause = False
    while True:
        _, img = cam.read()
        cv2.imshow('input', img)
        ret = detector.run(img)
        time_str = ''
        for stat in time_stats:
          time_str = time_str + '{} {:.3f}s |'.format(stat, ret[stat])
        print(time_str)
        if cv2.waitKey(1) == 27:
            return  # esc to quit
  else:
    if os.path.isdir(opt.demo):
      image_names = []
      ls = os.listdir(opt.demo)
      for file_name in sorted(ls):
          ext = file_name[file_name.rfind('.') + 1:].lower()
          if ext in image_ext:
              image_names.append(os.path.join(opt.demo, file_name))
    else:
      image_names = [opt.demo]
    
    results = list()
    image_names.sort()
    for (image_name) in image_names:
      ret = detector.run(image_name)
      time_str = ''
      for stat in time_stats:
        time_str = time_str + '{} {:.3f}s |'.format(stat, ret[stat])
      print(time_str)

      '''
      for cls_num in range(1,11):
        bboxs = ret['results'][cls_num]

        for box in bboxs:
          res = {'name': image_name.split('/')[-1],
                   'timestamp': 1000,
                   'category': cls_name[cls_num -1 ],
                   'bbox': [float(box[0]), float(box[1]), float(box[2]), float(box[3])],
                   'score': float(box[4]),
                   }
          results.append(res)
      #print(results)
    json.dump(results, open('results.json', 'w'), indent=4, separators=(',', ': '))
    '''
if __name__ == '__main__':
  opt = opts().init()

  opt.use_tensorrt = False
  opt.engine_file = 'trt/plusai_dlav0_960.trt'
  opt.engine_file = '/home/zhaozhe/packages/drive/opt/relwithdebinfo/cache/'
  opt.engine_file +='8cd9e1bcd6a6f200a897fad22c60d173.ecebe0f4b62c527a1f7b8be1680c2d66.5105.7.5.0.engine'
  demo(opt)
