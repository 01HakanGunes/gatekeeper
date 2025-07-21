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
