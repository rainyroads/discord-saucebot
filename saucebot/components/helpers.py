def make_utf8_safe(string: str):
    """
    Filters invalid characters from an input string

    Ensures the content is safe for logging and console output
    """
    if not string:
        return ""

    return bytes(string, 'utf-8').decode('utf-8', 'ignore')


def truncate(text: str, max_length: int) -> str:
    """
    Truncates a string to a maximum length and adds ellipses if it's too long.
    """
    if not text:
        return text

    if len(text) <= max_length:
        return text
    else:
        return text[:max_length - 3] + '...'


def codewrap(text: str) -> str:
    """
    Wraps text in code blocks
    """
    text = str(text).replace("`", "\\`")
    return f"```{text}```"


def escape_markdown(input_text: str):
    """
    Escapes any Markdown formatting in a provided string
    Args:
        input_text: The text to process

    Returns:
        str
    """
    # Escape any formatting tags from the users name
    input_text = input_text.replace("\\", "\\\\")
    input_text = input_text.replace("*", "\\*")
    input_text = input_text.replace("_", "\\_")
    input_text = input_text.replace("`", "\\`")
    input_text = input_text.replace("#", "\\#")
    input_text = input_text.replace("-", "\\-")

    return input_text
