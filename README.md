# Simple Tool for Human Keypoints Annotation
forked from [liruilong940607/AnnoSystem](https://github.com/liruilong940607/AnnoSystem)

### How to use

1. set your data dir and output dir. Line 22. & Line.23. in `main.py`
```python
ROOT_DIR = '/Users/dalong/workspace/ECCV2018/materials/2_result'
ANNO_DIR = '/Users/dalong/workspace/ECCV2018/materials/AnnoSystem/annos/2_result'
``` 
If you are annotating images in multiple subfolders at the same time (e.g. multi view data)
1) split the data into subfolders
2) run multiple scripts and use --dir subfolder1
3) annotate in multiple windows side by side

To run the script:
```bash
python main.py [--dir subfolder]
```

2. Dependence
```
    python3
    pyqt5 : pip3 install pyqt5
```
3. Shortcuts
```
    Q/A: Next/Previous Image
    D  : Next Person in This Image 
    W/R: Next/Previous Body Part of current Person 
```
