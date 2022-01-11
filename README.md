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
you'd use *[7,10,17]/42*. If not only the 42th frame is interesting for you, but all frames from
42 up to the 55th frame, specifying a range instead would work. A range is specified similar to
how slicing works in Python. *[7,10,17]/42:56* would work in our example. The range starts at
the 42th frame (*inclusive*) and stops just before the 56th frame (*exclusive*). Per default, the
stepsize is *1*, *42:56:2* would select every other frame and *42:56:-1* would give you the frames
in reverse order.
You can provide multiple of these expressions and receive the frames in the order of your expressions.
Have a look at the section [Expressions](#expressions-in-detail) or the documentation for the `YCBVideoLoader.frames()`
method for more ways and examples of how to specify the frames you're interested in.

The `data_syn` directory is also handled as a frame sequence, *\*/42* therefore would also include
the 42th frame from the `data_syn` frame sequence. Leaving exactly this one out can be achieved
with *data/42*, i.e. gets you the 42th frame for each frame sequence except the `data_syn` frame
sequence. Contrarily, *data_syn/42* gets you just this single frame.

Because the dataset is huge (~273 GB), it wouldn't make much sense to load all the data into memory
at once, therefore, frames are loaded one at a time. Especially in case your working with just a
subset of all the data from the dataset, e.g. having only the frame sequences 0001 - 0010 on your
disk, you'd want to be sure that the data is really available when you start working with the
frames. Therefore, after you specify all the frames you need by frame selection expression(s),
an automatic check is made to ensure that all the frames are on your disk and you didn't forget to put
e.g. frame sequence 0010 on your disk. This is especially helpful since the dataset is of most use
for machine learning tasks. Getting a "file not found" error after hours of training could be very
frustrating.

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
  for frame in loader.frames([
    'data_syn/1',
    '1/[2,4,5]',
    '42/[3,4]',
    '42:56/[2,3]',
    '[2,3,4]/*',
    '*/:56:-1',
    '*/*']):
    # do something with the frame
  ```
* Via a file

  ```
  # frames.txt

  data_syn/1,
  1/[2,4,5],
  42/[3,4],
  42:56/[2,3],
  [2,3,4]/*,
  */:56:-1,
  */*
  ```

  ```python
  for frame in loader.frames('/path/to/frames.txt'):
      # do something with the frame
  ```

  If you provide a relative path, it is assumed that the file is located inside the dataset directory,
  e.g. `imagesets/train.txt`.

If you want the frames to be shuffled for e.g. training in machine learning, just set the corresponding
keyword argument to `True`. Optionally, you can set a *seed* to get the same shuffling result for each run:

```python
# setting the seed
random.seed(42)

for frame in loader.frames('imagesets/train.txt', shuffle=True):
    # do something with it
```

## Expressions in detail

Selection expressions consist of two parts: An expression for specifying one
or more frame sequences and an expression for specifying one or more frames.
A */* combines both parts: *\<FRAME_SEQUENCE_SELECTION\>/\<FRAME_SELECTION\>*.
Most expressions are valid for both frame sequences and frames:

* *42*: Selects a single element *42* (*"Single element expression"*)
* *[42,47,56]*: Selects a list of elements, the elements *42*, *47* and *56* in
  exactly the order specified (*"List expression"*)
* *42:47:1*: Selects the elements between element *42* (inclusive) upt to element
  *47* (exclusive), i.e. the elements *42*, *43*, *44*, *45* and *46*
  (*"Range expression"*)
* *\**: Selects *all* elements (*"Star expression"*)

Two "single element expressions" only apply to the selection of frame sequences:

* *data_syn*: Selects the frame sequence *data_syn* (i.e. the `data_syn` directory)
* *data*: Selects *all* frame sequences except the *data_syn* frame sequence
  (i.e. all the subdirectories in the `data` directory)

"List expressions" and "range expressions" can only contain "numbered" elements like
*42* or *47*, not *data_syn* or *data*.

"Range expressions" are quite comparable to the slicing operation in Python. Given the
expression *\<START\>:\<STOP\>:\<STEP\>*, all the elements *START*, *STOP* and *STEP* are
optional. If *START* is omitted, *START* equals the *smallest* *available* element,
if *STOP* is omitted, it equals the *largest* *available* element. If *STEP* is
omitted, the step size equals *1*. *START* and *STOP* both have to be *positive* integers,
*STEP* might also be a negative integer, which then would lead to reverse order of the specified
elements. Step sizes other than *1* or *-1* are also allowed, except a step size of *0*.

## Missing data

Working with only a subset of the dataset is no problem.

* Using a "star expression", you just get all *available* elements
* Using a "range expression", elements in between your range might not be there,
  for instance, if elements 42, 43 and 45 are there, but element 44 is missing
  and you specify *42:45*, you would get the elements 42 and 43. You only have to
  make sure that if you specify elements as start and/or stop, these elements are available.

So, in short, every time you "name" an element, it has to be there! Using a "list
expression" *[42,43,44,45]* in the former example would instantly result in an error,
since element 44 is *not* available. A "Star expressions" would not complain. Also,
"range expressions", where the start and stop or both are omitted (e.g *42:*, *:45* or *:*)
will not complain since all "named" elements are available. Be aware this also means,
that *you* are responsible for making sure that all elements you expect to be on your disk
are there in these cases.

By running

```shell
python -m ycbvideo /path/to/data
```

you can manually inspect and check the integrity of the portion of the dataset on your disk.

## Roadmap

* Perform tests also on Windows
* Make other data from the dataset easily accessible where useful
* Test, build and publish the package by using *GitHub Actions*
