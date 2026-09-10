"""Test LPIPS preprocessing and distance decisions without downloading weights."""

from contextlib import nullcontext
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np

from Pipelines.Screengetter.Functions.frame_similarity import _prepare_frame, not_similar
from Pipelines.Screengetter.Functions.create_reference import create_reference


class TestFrameSimilarity(unittest.TestCase):
    def test_rgb_normalization_and_shape(self):
        frame = np.zeros((8, 16, 3), dtype=np.uint8)
        frame[:, :, 2] = 255
        prepared = _prepare_frame(frame)
        self.assertEqual(prepared.shape, (1, 3, 224, 224))
        self.assertEqual(prepared.dtype, np.float32)
        np.testing.assert_array_equal(prepared[:, 0], 1.)
        np.testing.assert_array_equal(prepared[:, 1:], -1.)

    def test_lpips_distance_threshold(self):
        frame = np.zeros((8, 8, 3), dtype=np.uint8)
        model = Mock()
        torch = SimpleNamespace(from_numpy=Mock(), inference_mode=nullcontext)
        with patch.dict('sys.modules', {'torch': torch}), patch(
            'Pipelines.Screengetter.Functions.frame_similarity._load_model',
            return_value=(model, 'cpu')
        ):
            for distance, expected in [(0., False), (0.05, False), (0.1, False), (0.2, True)]:
                model.return_value.item.return_value = distance
                self.assertEqual(not_similar(frame, frame), expected)
            self.assertFalse(not_similar(frame, frame, 0.3))
            model.return_value.item.return_value = float('nan')
            with self.assertRaises(ValueError):
                not_similar(frame, frame)

    def test_invalid_threshold(self):
        for threshold in [float('nan'), float('inf'), -0.1]:
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                create_reference('unused', 'unused', similarity_threshold=threshold)
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                not_similar(None, None, threshold)
