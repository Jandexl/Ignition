"""Fixed, predeclared models. No target-driven feature selection or imputation."""
from dataclasses import dataclass, asdict
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from .schema import CONDITIONS, GEOMETRY

@dataclass(frozen=True)
class Config:
    geometry: tuple = ('sample_width_cm',)
    width_height_ratio: bool = False
    alpha: float = 1.0
    strategy: str = 'logo'
    n_splits: int = 3
    min_groups: int = 3
    holdout_investigation: str = ''
    plan_id: str = ''
    independence_review_id: str = ''
    comparability_review_id: str = ''
    geometry_rationale: str = ''
    frozen_before_evaluation: bool = False
    max_domain_distance: float = 0.35

    def check(self):
        if not set(self.geometry).issubset(GEOMETRY) or len(set(self.geometry)) != len(self.geometry):
            raise ValueError('Geometry must use unique allowed pre-outcome fields.')
        if self.width_height_ratio and not {'sample_width_cm', 'duct_height_cm'}.issubset(self.geometry):
            raise ValueError('Width/height ratio requires both verified dimensions.')
        if not np.isfinite(self.alpha) or self.alpha <= 0: raise ValueError('alpha must be positive.')
        if self.strategy not in ('logo', 'groupkfold', 'campaign', 'cross_scale'): raise ValueError('Unknown split strategy.')
        if self.min_groups < 3 or self.n_splits < 2: raise ValueError('At least three groups and two folds required.')
        if not np.isfinite(self.max_domain_distance) or not 0 < self.max_domain_distance <= 1:
            raise ValueError('Distance tolerance must be explicitly set in (0,1].')
        if not all((self.plan_id, self.independence_review_id, self.comparability_review_id, self.frozen_before_evaluation)):
            raise ValueError('A frozen evaluation plan, independence review and comparability review are required.')
        if self.geometry and not self.geometry_rationale: raise ValueError('Geometry rationale is required.')

    def to_dict(self): return asdict(self)

class PhysicsFeatures(BaseEstimator, TransformerMixin):
    def __init__(self, ratio=False): self.ratio = ratio
    def fit(self, X, y=None): return self
    def transform(self, X):
        out = X.copy()
        if self.ratio:
            if (out.duct_height_cm <= 0).any(): raise ValueError('Nonpositive duct height')
            out['width_height_ratio'] = out.sample_width_cm / out.duct_height_cm
        return out


def features(name, cfg):
    numeric = list(CONDITIONS)
    categorical = ['material', 'flow_direction']
    if name == 'geometry_ridge':
        numeric += list(cfg.geometry)
        if cfg.width_height_ratio: numeric += ['width_height_ratio']
    return numeric, categorical


def build(name, cfg):
    if name == 'mean': return DummyRegressor(strategy='mean')
    if name not in ('condition_ridge', 'geometry_ridge'): raise ValueError('Unknown model')
    num, cat = features(name, cfg)
    preprocess = ColumnTransformer([
        ('numeric', StandardScaler(), num),
        ('categorical', OneHotEncoder(handle_unknown='error', sparse_output=False), cat)], remainder='drop')
    return Pipeline([('physics', PhysicsFeatures(name == 'geometry_ridge' and cfg.width_height_ratio)),
                     ('preprocess', preprocess), ('regression', Ridge(alpha=cfg.alpha))])
