import numpy as np
from malaya.text.function import (
    simple_textcleaning,
    classification_textcleaning,
    entities_textcleaning,
    language_detection_textcleaning,
    tag_chunk,
)
from malaya.function import add_neutral as neutral
from herpetologist import check_type
from typing import List


class BAYES:
    def __init__(
        self,
        multinomial,
        label,
        vectorize,
        bpe,
        subword_mode,
        cleaning = simple_textcleaning,
    ):
        self._multinomial = multinomial
        self._label = label
        self._vectorize = vectorize
        self._bpe = bpe
        self._subword_mode = subword_mode
        self._cleaning = cleaning

    def _classify(self, strings):
        strings = [self._cleaning(string) for string in strings]
        subs = [
            ' '.join(s)
            for s in self._bpe.encode(strings, output_type = self._subword_mode)
        ]
        vectors = self._vectorize.transform(subs)
        return self._multinomial.predict_proba(vectors)

    def _predict(self, strings, add_neutral = False):
        results = self._classify(strings)

        if add_neutral:
            result = neutral(results)
            label = self._label + ['neutral']
        else:
            label = self._label

        return [label[result] for result in np.argmax(results, axis = 1)]

    def _predict_proba(self, strings, add_neutral = False):
        results = self._classify(strings)

        if add_neutral:
            results = neutral(results)
            label = self._label + ['neutral']
        else:
            label = self._label

        outputs = []
        for result in results:
            outputs.append({label[i]: result[i] for i in range(len(result))})
        return outputs


class BINARY_BAYES(BAYES):
    def __init__(
        self,
        multinomial,
        label,
        vectorize,
        bpe,
        subword_mode,
        cleaning = simple_textcleaning,
    ):
        BAYES.__init__(
            self, multinomial, label, vectorize, bpe, subword_mode, cleaning
        )

    @check_type
    def predict(self, strings: List[str], add_neutral: bool = True):
        """
        Classify a string.

        Parameters
        ----------
        strings: List[str]
        add_neutral: bool, optional (default=True)
            if True, it will add neutral probability.

        Returns
        -------
        result: List[str]
        """

        return self._predict(strings = strings, add_neutral = add_neutral)

    @check_type
    def predict_proba(self, strings: List[str], add_neutral: bool = True):
        """
        Classify a list of strings.

        Parameters
        ----------
        strings: List[str]
        add_neutral: bool, optional (default=True)
            if True, it will add neutral probability.

        Returns
        -------
        result: List[dict[str, float]]
        """

        return self._predict_proba(strings = strings, add_neutral = add_neutral)


class MULTICLASS_BAYES(BAYES):
    def __init__(
        self,
        multinomial,
        label,
        vectorize,
        bpe,
        subword_mode,
        cleaning = simple_textcleaning,
    ):
        BAYES.__init__(
            self, multinomial, label, vectorize, bpe, subword_mode, cleaning
        )

    @check_type
    def predict(self, strings: List[str]):
        """
        Classify a string.

        Parameters
        ----------
        strings: List[str]

        Returns
        -------
        result: List[str]
        """

        return self._predict(strings = strings)

    @check_type
    def predict_proba(self, strings: List[str]):
        """
        Classify a list of strings.

        Parameters
        ----------
        strings: List[str]

        Returns
        -------
        result: List[dict[str, float]]
        """

        return self._predict_proba(strings = strings)


class MULTILABEL_BAYES(BAYES):
    def __init__(
        self,
        multinomial,
        label,
        vectorize,
        bpe,
        subword_mode,
        cleaning = simple_textcleaning,
    ):
        BAYES.__init__(
            self, multinomial, label, vectorize, bpe, subword_mode, cleaning
        )

    @check_type
    def predict(self, strings: List[str]):
        """
        Classify a string.

        Parameters
        ----------
        strings: List[str]

        Returns
        -------
        result: List[List[str]]
        """

        result = self._classify(strings = strings)
        arounded = np.around(result)

        results = []
        for i, row in enumerate(result):
            nested_results = []
            for no, label in enumerate(self._label):
                if arounded[i, no]:
                    nested_results.append(label)
            results.append(nested_results)
        return results

    @check_type
    def predict_proba(self, strings: List[str]):
        """
        Classify a list of strings.

        Parameters
        ----------
        strings: list

        Returns
        -------
        result: List[dict[str, float]]
        """

        result = self._classify(strings = strings)
        arounded = np.around(result)

        results = []
        for i, row in enumerate(result):
            nested_results = {}
            for no, label in enumerate(self._class_names):
                nested_results[label] = row[no]
            results.append(nested_results)
        return results


class LANGUAGE_DETECTION:
    def __init__(self, model, lang_labels):
        self._model = model
        self._labels = list(lang_labels.values())

    def _predict(self, strings):
        strings = [
            language_detection_textcleaning(string) for string in strings
        ]
        return self._model.predict(strings)

    @check_type
    def predict(self, strings: List[str]):
        """
        Classify a string.

        Parameters
        ----------
        strings: List[str]

        Returns
        -------
        result: List[str]
        """

        result_labels, result_probs = self._predict(strings)
        return [label[0].replace('__label__', '') for label in result_labels]

    @check_type
    def predict_proba(self, strings: List[str]):
        """
        Classify a list of strings.

        Parameters
        ----------
        strings: List[str]

        Returns
        -------
        result: List[dict[str, float]]
        """

        result_labels, result_probs = self._predict(strings)
        outputs = []
        for no, labels in enumerate(result_labels):
            result = {label: 0.0 for label in self._labels}
            for no_, label in enumerate(labels):
                label = label.replace('__label__', '')
                result[label] = result_probs[no][no_]
            outputs.append(result)
        return outputs
