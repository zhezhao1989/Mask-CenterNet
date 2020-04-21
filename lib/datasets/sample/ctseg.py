from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import torch.utils.data as data
import numpy as np
import torch
import json
import cv2
import os
from utils.image import flip, color_aug
from utils.image import get_affine_transform, affine_transform
from utils.image import gaussian_radius, draw_umich_gaussian, draw_msra_gaussian
from utils.image import draw_dense_reg
import math


class CTSegDataset(data.Dataset):
    def _coco_box_to_bbox(self, box):
        bbox = np.array([box[0], box[1], box[0] + box[2], box[1] + box[3]],
                        dtype=np.float32)
        return bbox

    def _get_border(self, border, size):
        i = 1
        while size - border // i <= border // i:
            i *= 2
        return border // i

    def __getitem__(self, index):
        img_id = self.images[index]
        file_name = self.coco.loadImgs(ids=[img_id])[0]['file_name']
        img_path = os.path.join(self.img_dir, file_name)
        ann_ids = self.coco.getAnnIds(imgIds=[img_id])
        anns = self.coco.loadAnns(ids=ann_ids)

        # delete not person and crowd
#        anns = list(filter(lambda x:x['category_id'] in self._valid_ids and x['iscrowd']!= 1 , anns))
        anns = list(filter(lambda x:x['category_id'] in self._valid_ids , anns))


        num_objs = min(len(anns), self.max_objs)
        img = cv2.imread(img_path)

        height, width = img.shape[0], img.shape[1]
        c = np.array([img.shape[1] / 2., img.shape[0] / 2.], dtype=np.float32)
        if self.opt.keep_res:
            input_h = (height | self.opt.pad) + 1
            input_w = (width | self.opt.pad) + 1
            s = np.array([input_w, input_h], dtype=np.float32)
        else:
            s = max(img.shape[0], img.shape[1]) * 1.0
            input_h, input_w = self.opt.input_h, self.opt.input_w

        flipped = False
        if self.split == 'train':
            if not self.opt.not_rand_crop:
                s = s * np.random.choice(np.arange(0.6, 1.4, 0.1))
                w_border = self._get_border(128, img.shape[1])
                h_border = self._get_border(128, img.shape[0])
                c[0] = np.random.randint(low=w_border, high=img.shape[1] - w_border)
                c[1] = np.random.randint(low=h_border, high=img.shape[0] - h_border)
            else:
                sf = self.opt.scale
                cf = self.opt.shift
                c[0] += s * np.clip(np.random.randn() * cf, -2 * cf, 2 * cf)
                c[1] += s * np.clip(np.random.randn() * cf, -2 * cf, 2 * cf)
                s = s * np.clip(np.random.randn() * sf + 1, 1 - sf, 1 + sf)

            if np.random.random() < self.opt.flip:
                flipped = True
                img = img[:, ::-1, :]
                c[0] = width - c[0] - 1

        trans_input = get_affine_transform(
            c, s, 0, [input_w, input_h])
        inp = cv2.warpAffine(img, trans_input,
                             (input_w, input_h),
                             flags=cv2.INTER_LINEAR)
        test_im = inp.copy()

        inp = (inp.astype(np.float32) / 255.)

        if self.split == 'train' and not self.opt.no_color_aug:
            color_aug(self._data_rng, inp, self._eig_val, self._eig_vec)

        inp = (inp - self.mean) / self.std
        inp = inp.transpose(2, 0, 1)

        output_h = input_h // self.opt.down_ratio
        output_w = input_w // self.opt.down_ratio
        num_classes = self.num_classes
        trans_output = get_affine_transform(c, s, 0, [output_w, output_h])
        trans_seg_output = get_affine_transform(c, s, 0, [output_w, output_h])
        hm = np.zeros((num_classes, output_h, output_w), dtype=np.float32)
        wh = np.zeros((self.max_objs, 2), dtype=np.float32)
        reg = np.zeros((self.max_objs, 2), dtype=np.float32)
        seg = np.ones((self.max_objs, output_h, output_w), dtype=np.float32)*255
        ind = np.zeros((self.max_objs), dtype=np.int64)
        reg_mask = np.zeros((self.max_objs), dtype=np.uint8)

        draw_gaussian = draw_msra_gaussian if self.opt.mse_loss else \
            draw_umich_gaussian

        gt_det = []
        if num_objs > 0:
            iii = np.random.randint(0, num_objs)

        for k in range(num_objs):
            ann = anns[k]
            bbox = self._coco_box_to_bbox(ann['bbox'])
            cls_id = int(self.cat_ids[ann['category_id']])
            #ann['segmentation']['counts'] = ann['segmentation']['counts'].encode(encoding='UTF-8')
            if ann['segmentation'] != None:
                segment = self.coco.annToMask(ann)
            if flipped:
                bbox[[0, 2]] = width - bbox[[2, 0]] - 1
                if ann['segmentation']!=None:
                    segment = segment[:, ::-1]
            '''
            if ann['segmentation']!=None and k == iii:
                seg_index = cv2.warpAffine(segment, trans_input,
                                     (input_w, input_h),
                                     flags=cv2.INTER_LINEAR)
                seg_index = seg_index > 0
                color = np.array([[255,0,0]])
                test_im[seg_index] = test_im[seg_index]*0.2 + color * 0.8
            '''

            bbox[:2] = affine_transform(bbox[:2], trans_output)
            bbox[2:] = affine_transform(bbox[2:], trans_output)
            bbox[[0, 2]] = np.clip(bbox[[0, 2]], 0, output_w - 1)
            bbox[[1, 3]] = np.clip(bbox[[1, 3]], 0, output_h - 1)
            if ann['segmentation']!=None:
                segment= cv2.warpAffine(segment, trans_seg_output,
                                     (output_w, output_h),
                                     flags=cv2.INTER_LINEAR)
                segment = segment.astype(np.float32)
            h, w = bbox[3] - bbox[1], bbox[2] - bbox[0]
            if h > 0 and w > 0:
                radius = gaussian_radius((math.ceil(h), math.ceil(w)))
                radius = max(0, int(radius))
                radius = self.opt.hm_gauss if self.opt.mse_loss else radius
                ct = np.array(
                    [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2], dtype=np.float32)
                ct_int = ct.astype(np.int32)
                draw_gaussian(hm[cls_id], ct_int, radius)
                wh[k] = 1. * w, 1. * h
                ind[k] = ct_int[1] * output_w + ct_int[0]
                reg[k] = ct - ct_int
                reg_mask[k] = 1
                pad_rate = 0.1
                if ann['segmentation']!=None:
                    segment_mask = np.ones_like(segment)
                    x,y = (np.clip([ct[0] - (1 + pad_rate)*w/2 ,ct[0] + (1 + pad_rate)*w/2 ],0,output_w - 1)).astype(np.int), \
                          (np.clip([ct[1] - (1 + pad_rate)*h/2 , ct[1] + (1 + pad_rate)*h/2],0,output_h - 1)).astype(np.int)
                    segment_mask[y[0]:y[1],x[0]:x[1]] = 0
                    segment[segment>0] = 1
                    segment[segment_mask == 1] = 255
                    seg[k] = segment
                if ann['segmentation']!=None:
                    pass
                    #cv2.rectangle(
                    #      segment, (bbox[0], bbox[1]), (bbox[0], bbox[1]), (255,0,0), 2)
                    #print(file_name.split('/')[-1])
                    #cv2.imwrite('/home/zhe.zhao/'+ file_name.split('/')[-1].split('.')[0]+str(k)+'.jpg',segment*255)
                    #cv2.imwrite('/home/zhe.zhao/0_'+ file_name.split('/')[-1].split('.')[0]+str(k)+'.jpg',test_im)
                    #cv2.waitKey(0)
                    #seg_mask[k] = segment_mask

                #print(np.sum(segment)/np.sum(segment_mask)) ## pos / neg

                gt_det.append([ct[0] - w / 2, ct[1] - h / 2,
                               ct[0] + w / 2, ct[1] + h / 2, 1, cls_id])

        #cv2.imwrite('/home/zhe.zhao/'+ file_name.split('/')[-1],test_im)

        ret = {'input': inp, 'hm': hm, 'reg_mask': reg_mask, 'ind': ind,
               'wh': wh ,'reg': reg ,'seg':seg }


        if self.opt.debug > 0 or not self.split == 'train':
            gt_det = np.array(gt_det, dtype=np.float32) if len(gt_det) > 0 else \
                np.zeros((1, 6), dtype=np.float32)
            meta = {'c': c, 's': s, 'gt_det': gt_det, 'img_id': img_id}
            ret['meta'] = meta
        return ret