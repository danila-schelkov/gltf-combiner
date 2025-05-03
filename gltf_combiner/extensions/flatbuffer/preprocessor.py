from collections import OrderedDict


class Preprocessor:
    @classmethod
    def preprocess_data(cls, data: any):
        """
        The `preprocess_data` function takes in any data and applies specific preprocessing steps based on
        the data type.

        :param data: The parameter "data" can be of any type.
        :type data: any
        :return: Preprocessed data
        """

        if isinstance(data, list):
            if len(data) == 0:
                return None
            return cls._preprocess_list(data)
        elif isinstance(data, dict):
            if len(data.keys()) == 0:
                return None
            return cls._preprocess_dict(data)
        elif isinstance(data, float):
            return round(data, 6)
        elif isinstance(data, int):
            if data == -1:
                return None

        return data

    @classmethod
    def _preprocess_list(cls, data: list) -> list:
        """
        The function preprocess_list takes a list of data, removes any None values, and applies a
        preprocessing function to each remaining value before returning the processed list.

        :param data: The parameter `data` is a list of values that need to be preprocessed
        :return: preprocessed list.
        """

        result = []

        for value in data:
            pre_value = cls.preprocess_data(value)

            if pre_value is None:
                continue
            else:
                result.append(pre_value)

        return result

    @classmethod
    def _preprocess_dict(cls, data: dict) -> dict:
        """
        The function preprocesses a dictionary by removing any key-value pairs where the value is None and
        applying a preprocessing function to the remaining values.

        :param data: A dictionary containing key-value pairs
        :type data: dict
        :return: Preprocessed dictionary.
        """

        result = OrderedDict()

        for key, value in data.items():
            pre_value = cls.preprocess_data(value)

            if pre_value is None:
                continue
            else:
                result[key] = pre_value

        return result
