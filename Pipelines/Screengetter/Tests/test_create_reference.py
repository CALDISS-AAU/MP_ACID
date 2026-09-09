"""Test reference generation with small, lossless video fixtures."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import cv2
import numpy as np

from Pipelines.Screengetter.Functions.arrays_from_frames import extract_framearrays
from Pipelines.Screengetter.Functions.create_reference import create_reference


class TestCreateReference(unittest.TestCase):
    def _write_video(self, path, samples):
        height, width = samples[0].shape[:2]
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"FFV1"), 1, (width, height))
        self.assertTrue(writer.isOpened(), "Lossless FFV1 video writer is unavailable")
        try:
            for frame in samples:
                for _ in range(5):
                    writer.write(frame)
        finally:
            writer.release()

    def test_sampling_threshold_resolution_and_outputs(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            input_dir = root / "videos"
            input_dir.mkdir()
            output_dir = root / "reference"

            black = np.zeros((8, 8, 3), dtype=np.uint8)
            half_white = black.copy()
            half_white[:4] = 255
            white = np.full_like(black, 255)
            red = black.copy()
            red[:, :, 2] = 255
            self._write_video(input_dir / "a.avi", [black, half_white, white, red, red])
            self._write_video(input_dir / "b.AVI", [np.zeros((16, 16, 3), dtype=np.uint8)])
            (input_dir / "notes.txt").write_text("Ignore non-video files")
            (input_dir / "folder.mp4").mkdir()

            # Cached dimensions must not override the current input videos.
            output_dir.mkdir()
            (output_dir / "resolutions.json").write_text(
                '[{"width": 100, "height": 100, "total": 10000}]'
            )
            lookup = create_reference(input_dir, output_dir)

            self.assertEqual(
                [(entry["source_video"], entry["timestamp_s"]) for entry in lookup],
                [("a.avi", 0), ("a.avi", 10), ("a.avi", 15), ("a.avi", 20), ("b.AVI", 0)]
            )
            self.assertEqual(json.loads((output_dir / "reference_lookup.json").read_text()), lookup)
            self.assertEqual(len(list(output_dir.glob("*.png"))), 5)
            self.assertEqual(len(list(output_dir.glob("*.npy"))), 5)
            for entry in lookup:
                array = np.load(output_dir / entry["npy_path"], allow_pickle=False)
                image = cv2.imread(str(output_dir / entry["png_path"]))
                self.assertEqual(array.shape, (8, 8, 3))
                np.testing.assert_array_equal(image, array)
                self.assertEqual(entry["color_order"], "BGR")
            np.testing.assert_array_equal(np.load(output_dir / lookup[2]["npy_path"]), red)

            # Event extraction must use the same size, including single samples.
            intervals = extract_framearrays(
                input_dir / "b.AVI", [range(0, 1000)],
                standardize_resolution = True,
                use_resolution = {"width": 8, "height": 8}
            )
            self.assertEqual(intervals[0][0][2].shape, (8, 8, 3))

    def test_retained_frames_are_shared_across_videos(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            black = np.zeros((8, 8, 3), dtype=np.uint8)
            half_white = black.copy()
            half_white[:4] = 255
            self._write_video(root / "a.avi", [black])
            self._write_video(root / "b.avi", [black, half_white])

            lookup = create_reference(root, root / "output")

            # Neither an identical frame nor exactly 50% change is retained,
            # including the first sample of a later video.
            self.assertEqual(
                [(entry["source_video"], entry["timestamp_s"]) for entry in lookup],
                [("a.avi", 0)]
            )

    def test_missing_or_empty_input(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(NotADirectoryError):
                create_reference(root / "missing", root / "output")
            with self.assertRaisesRegex(ValueError, "No video files"):
                create_reference(root, root / "output")

    def test_image_write_failure_is_reported(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_video(root / "video.avi", [np.zeros((8, 8, 3), dtype=np.uint8)])
            with patch(
                "Pipelines.Screengetter.Functions.create_reference.cv2.imwrite",
                return_value = False
            ):
                with self.assertRaises(OSError):
                    create_reference(root, root / "output")
            self.assertFalse((root / "output" / "reference_lookup.json").exists())


if __name__ == "__main__":
    unittest.main()
