Experiment to replace `file` based file classification with a python version (well, as little
pure python as possible). The goals are:
* classify files crudely as binary / text, where binary means ELF / mach-O, and text is
  either utf-8, utf-16 or iso-88590-1 (no cp1252 yet).
* read as few bytes as possible to make the decision

The idea is basically:
* First classify ELF / macho-O (i.e. binary to relocate)
* Then classify utf-8 and utf-16 in that order
  * utf-8 is the most likely encoding and has exponentially low false positive rate with file size
  * read in chunks and bail on first decode error -- this almost always happens in the
    first few bytes is much faster compared to the `file` utility which reads all bytes.
* Then try iso-8859-1. Python does not raise decoding errors for it, so we use a heuristic:
  it is not iso-8859-1 if it contains null bytes or control characters 0x7F-0x9F.

On my NVME disk with a warm cache, this is well over 10x faster than a batched `file` command, and
classifies:

```
714782 total files
513748 utf-8 (including pure ascii)
   662 iso-8859-1
    27 utf-16
```

in 23.8s total time, consuming 6259353564 bytes of 129642132904 (so only 4.83% is read).

So it runs at about 250MB/s.