# ycbvideo

Python package for loading the data from the YCB-Video Dataset.
It's a very large dataset made for computer vision task like *6D object pose estimation* or
*semantic segmentation*.
You can find more information and a download link for the dataset
[here](https://rse-lab.cs.washington.edu/projects/posecnn/).

It allows access to the *frames*, located either in `data` or the `data_syn` folders. A frame
here corresponds to all the information available for one portion of time, i.e. not only the color
image, but the color/depth/label images and for the frames in `data` also the bounding box coordinates.
Frames are grouped in *frame sequences* of consecutive frames.
Frames and frame sequences can be specified by *frame selection expressions*.

Example:

Frame 42 from frame sequence 7 corresponds to the following data

* `data/0007/000042-color.png`
* `data/0007/000042-depth.png`
* `data/0007/000042-label.png`
* `data/0007/000042-box.txt`

and can be specified by the frame selection expression *7/42* to just specify this single frame.
If you'd like to specify e.g. the 42th frame for each *available* frame sequence, you could express
this by *\*/42*. If you're interested in only the 42th frame from the frame sequences 7, 10 and 17,
you'd use *[7,10,17]/42*. You can provide multiple of these expressions and receive the frames in
the order of your expressions. Have a look at the documentation for the `YCBVideoLoader.frames()`
method for more ways and examples of how to specify the frames you're interested in.

The `data_syn` directory is also handled as a frame sequence, *\*/42* therefore would also include
the 42th frame from the `data_syn` frame sequence.

Because the dataset is huge (~273 GB), it wouldn't make much sense to load all the data into memory
at once, therefore, frames are loaded one at a time. Especially in case your working with just a
subset of all the data from the dataset, e.g. having only the frame sequences 0001 - 0010 on your
disk, you'd want to be sure that the data is really available when you start working with the
frames. Therefore, after you specify all the frames you need by frame selection expression(s),
an automatic check is made to ensure that all the frames are on your disk and you didn't forget to put
e.g. frame sequence 0010 on your disk. This is especially helpful since the dataset is of most use
for machine learning tasks. Getting a "file not found" error after hours of training could be very
frustrating.

By running

```shell
python -m ycbvideo /path/to/data
```

you can manually inspect and check the integrity of the portion of the dataset on your disk.

## Installation

It's published at [PYPI](https://pypi.org/project/ycbvideo/), just use `pip install ycbvideo` to
install it. Python >= 3.8 is required.

## Usage

First, import the package and create a loader. Provide the path to the dataset directory.
Do not modify the data afterwards!

```python
import ycbvideo

loader = ycbvideo.YCBVideoLoader('/path/to/data')
```

### Accessing Frames

You can specify the frames by frame selection expressions, either via a list of such expressions
or by providing a file comprised of those expressions, one expression per line.

* Via a list

  ```python
  for frame in loader.frames(['data_syn/1', '[1]/[2,4,5]', 'data_syn/[3,4]', '[2,3,4]/*', '*/*'):
      // do something with the frame
  ```
* Via a file

  ```
  # frames.txt

  data_syn/1
  [1]/[2,4,5]
  data_syn/[3,4]
  [2,3,4]/*
  */*
  ```

  ```python
  for frame in loader.frames('/path/to/frames.txt'):
      // do something with the frame
  ```

  If you provide a relative path, it is assumed that the file is located inside the dataset directory,
  e.g. `imagesets/train.txt`.

If you want the frames to be shuffled for e.g. training in machine learning, just set the corresponding
keyword argument to `True`. Optionally, you can set a *seed* to get the same shuffling result for each run:

```python
# setting the seed
random.seed(42)

for frame in loader.frames('imagesets/train.txt', shuffle=True):
    // do something with it
```
