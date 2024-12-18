#!/usr/bin/env python3

# run the `file` executable on a list of files

import subprocess
import sys
from itertools import batched


def main(files: list, batch_size: int = 1000):
    total_files = len(files)
    processed_files = 0

    with open("file.txt", "w") as file:
        for batch_files in batched(files, batch_size):
            try:
                output = subprocess.check_output(
                    ["file", "--brief", "--mime-type", *batch_files]
                )
                mime_types = output.decode("utf-8").strip().splitlines()
                for filename, mime in zip(batch_files, mime_types):
                    mime_type, encoding = mime.split("/")
                    if mime_type == "text":
                        print(filename, file=file)

                processed_files += len(batch_files)
                progress = processed_files / total_files * 100
                sys.stderr.write(f"Progress: {progress:.2f}%\r")
                sys.stderr.flush()

            except subprocess.CalledProcessError as e:
                for filename in batch_files:
                    print(f"Error processing {filename}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main([path.strip() for path in open(sys.argv[1])])
