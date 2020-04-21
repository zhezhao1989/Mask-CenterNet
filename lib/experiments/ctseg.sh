nohup python main.py --task ctseg --dataset coco_seg --exp_id kitti_seg \
--batch_size 16 --num_epochs 140 --lr_step 90,120 --gpus 4,5,6,7 \
> ~/nohup.txt &
#--resume --load_model ../exp/ctseg/kitti_seg/model_last.pth \
#> ~/nohup.txt &
