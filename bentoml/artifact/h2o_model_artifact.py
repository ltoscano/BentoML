# Copyright 2019 Atalaya Tech, Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil

from bentoml.artifact import BentoServiceArtifact, BentoServiceArtifactWrapper
from bentoml.exceptions import MissingDependencyException


class H2oModelArtifact(BentoServiceArtifact):
    """Abstraction for saving/loading objects with h2o.save_model and h2o.load_model

    Args:
        name (str): Name for this h2o artifact..

    Raises:
        MissingDependencyException: h2o package is required to use H2o model artifact

    Example usage:

    >>> import h2o
    >>> h2o.init()
    >>>
    >>> from h2o.estimators.deeplearning import H2ODeepLearningEstimator
    >>> model_to_save = H2ODeepLearningEstimator(...)
    >>> # train model with data
    >>> data = h2o.import_file(...)
    >>> model_to_save.train(...)
    >>>
    >>> import bentoml
    >>> from bentoml.artifact import H2oModelArtifact
    >>> from bentoml.handlers import DataframeHandler
    >>>
    >>> @bentoml.artifacts([H2oModelArtifact('model')])
    >>> @bentoml.env(auto_pip_dependencies=True)
    >>> class H2oModelService(bentoml.BentoService):
    >>>
    >>>     @bentoml.api(DataframeHandler)
    >>>     def predict(self, df):
    >>>         hf = h2o.H2OFrame(df)
    >>>         predictions = self.artifacts.model.predict(hf)
    >>>         return predictions.as_data_frame()
    >>>
    >>> svc = H2oModelService()
    >>>
    >>> svc.pack('model', model_to_save)
    """

    @property
    def pip_dependencies(self):
        return ['h2o']

    def _model_file_path(self, base_path):
        return os.path.join(base_path, self.name)

    def pack(self, model):  # pylint:disable=arguments-differ
        return _H2oModelArtifactWrapper(self, model)

    def load(self, path):
        try:
            import h2o
        except ImportError:
            raise MissingDependencyException(
                "h2o package is required to use H2oModelArtifact"
            )

        h2o.init()
        model = h2o.load_model(self._model_file_path(path))
        return self.pack(model)


class _H2oModelArtifactWrapper(BentoServiceArtifactWrapper):
    def __init__(self, spec, model):
        super(_H2oModelArtifactWrapper, self).__init__(spec)
        self._model = model

    def save(self, dst):
        try:
            import h2o
        except ImportError:
            raise MissingDependencyException(
                "h2o package is required to use H2oModelArtifact"
            )

        h2o_saved_path = h2o.save_model(model=self._model, path=dst, force=True)
        shutil.move(h2o_saved_path, self.spec._model_file_path(dst))
        return

    def get(self):
        return self._model
