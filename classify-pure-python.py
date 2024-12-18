#!/usr/bin/env python3

import io
import os
import re
import stat
import sys


def print_progress(total_files, count_per_encoding, bytes_read, total_bytes):
    fraction = bytes_read / total_bytes * 100
    print(
        f"{total_files:7d} files: ",
        f"utf-8: {count_per_encoding['utf-8']:7d}, ",
        f"utf-16: {count_per_encoding['utf-16']:7d}, ",
        f"iso-8859-1: {count_per_encoding['iso-8859-1']:7d}. ",
        f"{bytes_read:12d} / {total_bytes:12d} bytes read " f"[{fraction: 6.2f}%]",
        file=sys.stderr,
    )


def run(spack_store: str):
    total_files = 0
    count_per_encoding = {
        "utf-8": 0,
        "utf-16": 0,
        "iso-8859-1": 0,
    }
    total_bytes = 0
    bytes_read = 0
    # in iso-8859-1 text files we don't expect null bytes and control chars \x7F-\x9F.
    not_iso8859_1_text = re.compile(b"[\x00\x7F-\x9F]")
    with open("all.txt", "w") as all_files, open("utf-8.txt", "w") as utf_8_files, open(
        "utf-16.txt", "w"
    ) as utf_16_files, open("iso-8859-1.txt", "w") as iso_8859_1_files:
        for root, _, files in os.walk(spack_store, topdown=False):
            for name in files:
                path = os.path.join(root, name)
                try:
                    s = os.lstat(path)
                except OSError:
                    continue
                # skip empty files, symlinks, dirs, and spack directories, as well as files that
                # cannot be opened
                if (
                    not s.st_size
                    or not stat.S_ISREG(s.st_mode)
                    or "/.spack/" in path
                    or "/.spack-db/" in path
                ):
                    continue
                try:
                    buf = open(path, "rb")
                except OSError:
                    continue
                total_bytes += s.st_size
                total_files += 1
                print(path, file=all_files)
                try:
                    # first check if this is an ELF or mach-o binary. (probably we don't have to
                    # care about the false positive where 0xcafebabe is used by java byte code)
                    try:
                        magic = buf.read(4)
                        if (
                            magic == b"\x7FELF"
                            or magic == b"\xFE\xED\xFA\xCE"  # 0xfeedface big endian
                            or magic == b"\xCE\xFA\xED\xFE"  # 0xfeedface little endian
                            or magic == b"\xFE\xED\xFA\xCF"  # 0xfeedfacf big endian
                            or magic == b"\xCF\xFA\xED\xFE"  # 0xfeedfacf little endian
                            or magic == b"\xCA\xFE\xBA\xBE"  # 0xcafebabe big endian
                            or magic == b"\xBE\xBA\xFE\xCA"  # 0xcafebabe little endian
                        ):
                            continue
                    finally:
                        bytes_read += buf.tell()
                    buf.seek(0)

                    # then try utf-* which has a very low false positive rate
                    for enc in ("utf-8", "utf-16"):
                        f = io.TextIOWrapper(buf, encoding=enc, errors="strict")
                        try:
                            while f.read(1024):
                                pass
                            if enc == "utf-8":
                                print(path, file=utf_8_files)
                            elif enc == "utf-16":
                                print(path, file=utf_16_files)
                            count_per_encoding[enc] += 1
                            break
                        except UnicodeError:
                            buf.seek(0)
                            pass
                        finally:
                            f.detach()
                            bytes_read += buf.tell()
                    # finally try iso-8859-1 which has a higher false positive rate
                    else:
                        try:
                            while data := buf.read(1024):
                                if not_iso8859_1_text.search(data):
                                    break
                            else:
                                print(path, file=iso_8859_1_files)
                                count_per_encoding["iso-8859-1"] += 1
                        finally:
                            bytes_read += buf.tell()

                finally:
                    buf.close()

                if total_files % 10000 == 0:
                    print_progress(
                        total_files, count_per_encoding, bytes_read, total_bytes
                    )

    print_progress(total_files, count_per_encoding, bytes_read, total_bytes)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <spack store>")
        sys.exit(1)
    run(sys.argv[1])
