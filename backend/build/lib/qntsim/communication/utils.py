import logging
from typing import Any, List


def to_binary(messages: List[str]):
    """Converts any character string to their binary equivalent.
    Args:
        messages (List[str]): List of messages to be converted into binary.

    Returns:
        strings (List[str]): List of binary equivalent of the input messages

    Example:
        print(string_to_binary(messages=['h'])
    """
    # strings = [''.join('0'*(8-len(bin(ord(char))[2:]))+bin(ord(char))[2:] for char in message) for _, message in messages.items()]
    _is_binary = all(char in "01" for message in messages for char in message)
    strings = messages if _is_binary else [
        "".join("{:08b}".format(ord(char)) for char in message)
        for message in messages
    ]
    logging.info("converted")

    return _is_binary, strings

def to_string(strings:List[str], _was_binary:bool):
    print(_was_binary)
    messages = ["".join(
                "{:c}".format(int(string[j * 8 : -~j * 8], 2)) for j in range(len(string) // 8)
            ) for string in strings] if not _was_binary else strings
    logging.info("converted back")

    return messages

def pass_(_: Any, returns: Any):
    return returns