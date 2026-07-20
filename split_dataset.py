# Simple script to split an ImageFolder-style dataset into train/val folders.
import os
import random
import shutil
from pathlib import Path

def split_dataset(root_dir, out_dir='data', val_ratio=0.2, seed=42):
    random.seed(seed)
    root = Path(root_dir)
    out = Path(out_dir)
    train_out = out / 'train'
    val_out = out / 'val'
    for p in [train_out, val_out]:
        p.mkdir(parents=True, exist_ok=True)

    classes = [d for d in root.iterdir() if d.is_dir()]
    for cls in classes:
        images = list(cls.glob('*'))
        random.shuffle(images)
        n_val = int(len(images) * val_ratio)
        val_imgs = images[:n_val]
        train_imgs = images[n_val:]
        train_cls_dir = train_out / cls.name
        val_cls_dir = val_out / cls.name
        train_cls_dir.mkdir(parents=True, exist_ok=True)
        val_cls_dir.mkdir(parents=True, exist_ok=True)
        for f in train_imgs:
            shutil.copy(f, train_cls_dir / f.name)
        for f in val_imgs:
            shutil.copy(f, val_cls_dir / f.name)
    print(f'Split complete. Output in {out.resolve()}')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=str, required=True, help='Path to original ImageFolder dataset (class subfolders)')
    parser.add_argument('--out', type=str, default='data', help='Output folder containing train/val')
    parser.add_argument('--val_ratio', type=float, default=0.2)
    args = parser.parse_args()
    split_dataset(args.root, args.out, args.val_ratio)
