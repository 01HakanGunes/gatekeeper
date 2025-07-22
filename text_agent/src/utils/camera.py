import base64
import cv2


def capture_photo(filename: str = "photo.jpg") -> bool:
    """
    Captures a single frame from the default laptop camera and saves it to the specified filename.
    Returns True if successful, False otherwise.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return False
    ret, frame = cap.read()
    cap.release()
    if ret:
        cv2.imwrite(filename, frame)
        return True
    return False


def image_file_to_base64(image_path: str) -> str:
    """
    Reads an image file and returns its base64-encoded string.
    """
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string
