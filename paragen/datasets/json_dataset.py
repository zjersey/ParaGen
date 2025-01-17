import json
import logging
logger = logging.getLogger(__name__)

from paragen.datasets import register_dataset
from paragen.datasets.in_memory_dataset import InMemoryDataset
from paragen.utils.data import count_sample_token
from paragen.utils.io import UniIO
from paragen.utils.runtime import progress_bar


@register_dataset
class JsonDataset(InMemoryDataset):
    """
    JsonDataset is an in-memory dataset for reading data saved with json.dumps.

    Args:
        path: data path to read
        sort_samples (bool): sort samples before running a task.
            It would be useful in inference without degrading performance.
        max_size: maximum size of loaded data
    """

    def __init__(self,
                 path,
                 sort_samples=False,
                 max_size=0):
        super().__init__(path, sort_samples=sort_samples, max_size=max_size)

    def _load(self):
        """
        Preload all the data into memory. In the loading process, data are preprocess and sorted.
        """
        fin = UniIO(path=self._path)
        self._data = []
        accecpted, discarded = 0, 0
        for i, sample in enumerate(progress_bar(fin, streaming=True, desc='Loading Samples')):
            if 0 < self._max_size <= i:
                break
            try:
                sample = sample.strip('\n')
                self._data.append(self._full_callback(sample))
                accecpted += 1
            except Exception:
                logger.warning('sample {} is discarded'.format(sample))
                discarded += 1
        if self._sort_samples:
            self._data.sort(key=lambda x: count_sample_token(x))
        self._length = len(self._data)
        logger.info(f'Totally accept {accecpted} samples, discard {discarded} samples')
        fin.close()

    def _callback(self, sample):
        """
        Callback for json data

        Args:
            sample: data in raw format

        Returns:
            sample (dict): a dict of samples consisting of parallel data of different sources
        """
        sample = json.loads(sample)
        return sample
