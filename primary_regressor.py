import random
from menpo.shape import PointCloud
import numpy as np
from primitive_regressor import PrimitiveRegressor
from util import transform_to_mean_shape
import util


class PrimaryRegressor:

    def __init__(self, n_pixels, n_fern_features, n_ferns, n_landmarks, mean_shape, kappa):
        self.n_ferns = n_ferns
        self.n_fern_features = n_fern_features
        self.n_features = n_pixels
        self.mean_shape = mean_shape
        self.kappa = kappa
        self.n_pixels = n_pixels
        self.n_landmarks = n_landmarks
        self.feature_extractor = PixelExtractor(n_pixels, n_landmarks, self.kappa)
        self.primitive_regressors = [PrimitiveRegressor(n_pixels, n_fern_features, n_ferns, n_landmarks) for i in range(n_ferns)]

    def extract_features(self, img, shape, mean_to_shape):
        return self.feature_extractor.extract_pixels(img, shape, mean_to_shape)

    def train(self, pixel_vectors, targets):
        n_samples = len(pixel_vectors)
        pixel_vals = np.transpose(pixel_vectors)

        pixel_averages = np.average(pixel_vals, axis=1)
        cov_pp = np.cov(pixel_vals)
        pixel_var_sum = np.diag(cov_pp)[:, None] + np.diag(cov_pp)

        i = 0
        for r in self.primitive_regressors:
            print 'Training regressor ', i
            i += 1
            r.train(pixel_vectors, targets, cov_pp, pixel_vals, pixel_averages, pixel_var_sum)
            for j in xrange(n_samples):
                offset = r.apply(pixel_vectors[j]).as_vector()
                targets[j] -= offset

    def apply(self, shape_indexed_features):
        res = PointCloud(np.zeros((self.n_landmarks, 2)), copy=False)

        for r in self.primitive_regressors:
            offset = r.apply(shape_indexed_features)
            res.points += offset.points
        return res


class PixelExtractor:
    def __init__(self, n_pixels, n_landmarks, kappa):
        self.lmark = np.random.randint(low=0, high=n_landmarks, size=n_pixels)
        self.pixel_coords = np.random.uniform(low=-kappa, high=kappa, size=n_pixels*2).reshape(n_pixels, 2)

    def extract_pixels(self, image, shape, mean_to_shape):
        offsets = mean_to_shape.apply(self.pixel_coords)
        ret = shape.points[self.lmark] + offsets
        return util.sample_image(image, ret)