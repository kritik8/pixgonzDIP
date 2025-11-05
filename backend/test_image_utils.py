from PIL import Image
import image_utils

# Load a test image
img = Image.open("test.jpg")  # Use a real image file

# Test each function
img_bc = image_utils.adjust_brightness_contrast(img, brightness=1.2, contrast=1.1)
img_gray = image_utils.to_grayscale(img)
img_blur = image_utils.apply_blur(img, radius=3)
img_sharp = image_utils.apply_sharpen(img, amount=1.5)
img_rot = image_utils.rotate_image(img, angle=45)
img_masked = image_utils.apply_mask(img, mask_type="circle")

# Save outputs to visually inspect
img_bc.save("test_brightness_contrast.jpg")
img_gray.save("test_grayscale.jpg")
img_blur.save("test_blur.jpg")
img_sharp.save("test_sharpen.jpg")
img_rot.save("test_rotated.jpg")
img_masked.save("test_masked.jpg")
print("All image operations saved for manual inspection.")
