import re

def parse_image_markers(text: str):
    """
    Parses [IMAGE: prompt] markers from a text stream.
    """
    pattern = r"\[IMAGE:(.*?)\]"
    markers = re.findall(pattern, text)
    clean_text = re.sub(pattern, "", text)
    return clean_text, markers
