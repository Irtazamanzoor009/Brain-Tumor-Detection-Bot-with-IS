from PIL import Image
from PIL.JpegImagePlugin import JpegImageFile
import os
import magic
import io


def check_image(image_path):
    # Check image integrity (is it a valid image)
    def check_image_integrity(image_path):
        try:
            with open(image_path, "rb") as img_file:
                img = Image.open(img_file)
                img.verify()  # Verify the image integrity
            return True
        except Exception as e:
            print(f"Image Integrity Check Failed: {e}")
            return False

    # Check metadata (remove EXIF data if present)
    def check_metadata(image_path):
        try:
            with open(image_path, "rb") as img_file:
                img = Image.open(img_file)
                if isinstance(img, JpegImageFile):
                    img.info.pop("exif", None)  # Remove EXIF data
            return True
        except Exception as e:
            print(f"Error removing metadata: {e}")
            return False

    # Check file type (match file extension with content type)
    def check_file_type(image_path):
        try:
            mime = magic.Magic(mime=True)
            file_type = mime.from_file(image_path)
            print(f"File type: {file_type}")
            if "image" in file_type:
                print("Valid image format")
                return True
            else:
                print("File is not a valid image")
                return False
        except Exception as e:
            print(f"Error checking file type: {e}")
            return False

    # Perform all checks
    if not os.path.exists(image_path):
        print("Image file does not exist.")
        return False

    print("Checking image integrity...")
    if not check_image_integrity(image_path):
        print("Image integrity check failed.")
        return False

    print("Checking metadata...")
    if not check_metadata(image_path):
        print("Metadata check failed.")
        return False

    print("Checking file type...")
    if not check_file_type(image_path):
        print("Invalid file type detected.")
        return False

    print("Image passed all checks!")
    return True


# Usage Example
image_path = r"C:\Users\Irtaza Manzoor\Desktop\Brain Tumor\4.jpeg"

if check_image(image_path):
    print("The image is clean and valid.")
else:
    print("The image failed one or more checks.")
