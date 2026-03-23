import cv2
import numpy as np

from src.processors.interfaces.ImagePreprocessor import ImagePreprocessor


class Levels(ImagePreprocessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        options = self.options

        def output_level(value, low, high, gamma):
            if value <= low:
                return 0
            if value >= high:
                return 255
            inv_gamma = 1.0 / gamma
            return (((value - low) / (high - low)) ** inv_gamma) * 255

        self.gamma = np.array(
            [
                output_level(
                    i,
                    int(255 * options.get("low", 0)),
                    int(255 * options.get("high", 1)),
                    options.get("gamma", 1.0),
                )
                for i in np.arange(0, 256)
            ]
        ).astype("uint8")

    def apply_filter(self, image, _file_path):
        return cv2.LUT(image, self.gamma)


class MedianBlur(ImagePreprocessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        options = self.options
        self.kSize = int(options.get("kSize", 5))

    def apply_filter(self, image, _file_path):
        return cv2.medianBlur(image, self.kSize)


class GaussianBlur(ImagePreprocessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        options = self.options
        self.kSize = tuple(int(x) for x in options.get("kSize", (3, 3)))
        self.sigmaX = int(options.get("sigmaX", 0))

    def apply_filter(self, image, _file_path):
        return cv2.GaussianBlur(image, self.kSize, self.sigmaX)


class Binarize(ImagePreprocessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        options = self.options
        self.method = options.get("method", "otsu")
        self.block_size = int(options.get("blockSize", 51))
        self.c = int(options.get("C", 10))

    def apply_filter(self, image, _file_path):
        if self.method == "normalize":
            ksize = self.block_size if self.block_size % 2 == 1 else self.block_size + 1
            bg = cv2.GaussianBlur(image, (ksize, ksize), 0)
            return cv2.divide(image, bg, scale=255)
        if self.method == "adaptive":
            return cv2.adaptiveThreshold(
                image,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                self.block_size,
                self.c,
            )
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
