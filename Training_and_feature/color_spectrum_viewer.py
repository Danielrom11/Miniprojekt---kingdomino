import cv2
import numpy as np
import matplotlib.pyplot as plt

def display_image_color_spectrums(image_path):
    """
    Display an image in different color spectrums using OpenCV.
    
    Color spectrums:
    1. BGR (Original)
    2. Grayscale
    3. Red channel (grayscale)
    4. Green channel (grayscale)
    5. Blue channel (grayscale)
    6. YUV
    7. HSV
    8. LAB
    """
    
    # Read the image
    image_bgr = cv2.imread(image_path)
    
    if image_bgr is None:
        print(f"Error: Could not read image from {image_path}")
        return
    
    # Create versions in different color spaces
    
    # 1. BGR (Original)
    spectrum_bgr = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)  # Convert to RGB for matplotlib
    
    # 2. Grayscale
    spectrum_gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    spectrum_gray = cv2.cvtColor(spectrum_gray, cv2.COLOR_GRAY2RGB)  # Convert back to RGB for display
    
    # 3-5. Individual RGB channels (grayscale)
    b_channel, g_channel, r_channel = cv2.split(image_bgr)
    
    # 6. YUV
    spectrum_yuv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2YUV)
    
    # 7. HSV (display as-is)
    spectrum_hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    
    # 8. LAB (display as-is, normalize for visualization)
    spectrum_lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    spectrum_lab = cv2.normalize(spectrum_lab, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    # 9. HSV to Grayscale (convert HSV back to BGR, then to grayscale)
    spectrum_hsv_bgr = cv2.cvtColor(spectrum_hsv, cv2.COLOR_HSV2BGR)
    spectrum_hsv_gray = cv2.cvtColor(spectrum_hsv_bgr, cv2.COLOR_BGR2GRAY)
    spectrum_hsv_gray = cv2.cvtColor(spectrum_hsv_gray, cv2.COLOR_GRAY2RGB)  # Convert back to RGB for display
    
    # 10-12. HSV individual channels (H, S, V)
    h_channel, s_channel, v_channel = cv2.split(spectrum_hsv)
    
    # Create subplot with 13 images (4x4 grid)
    fig, axes = plt.subplots(4, 4, figsize=(20, 16))
    axes = axes.flatten()
    
    axes[0].imshow(spectrum_bgr)
    axes[0].set_title('BGR (Original)')
    axes[0].axis('off')
    
    axes[1].imshow(spectrum_gray)
    axes[1].set_title('Grayscale')
    axes[1].axis('off')
    
    axes[2].imshow(r_channel, cmap='gray')
    axes[2].set_title('Red Channel (Grayscale)')
    axes[2].axis('off')
    
    axes[3].imshow(g_channel, cmap='gray')
    axes[3].set_title('Green Channel (Grayscale)')
    axes[3].axis('off')
    
    axes[4].imshow(b_channel, cmap='gray')
    axes[4].set_title('Blue Channel (Grayscale)')
    axes[4].axis('off')
    
    axes[5].imshow(spectrum_yuv)
    axes[5].set_title('YUV')
    axes[5].axis('off')
    
    axes[6].imshow(spectrum_hsv)
    axes[6].set_title('HSV (Combined)')
    axes[6].axis('off')
    
    axes[7].imshow(spectrum_lab)
    axes[7].set_title('LAB')
    axes[7].axis('off')
    
    axes[8].imshow(spectrum_hsv_gray)
    axes[8].set_title('HSV Grayscale')
    axes[8].axis('off')
    
    axes[9].imshow(h_channel, cmap='gray')
    axes[9].set_title('HSV - H Channel (Hue)')
    axes[9].axis('off')
    
    axes[10].imshow(s_channel, cmap='gray')
    axes[10].set_title('HSV - S Channel (Saturation)')
    axes[10].axis('off')
    
    axes[11].imshow(v_channel, cmap='gray')
    axes[11].set_title('HSV - V Channel (Value)')
    axes[11].axis('off')
    
    # Leave remaining slots empty
    for i in range(12, 16):
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Example: Display an image from the Trainingset folder
    # Change the image number as needed
    image_path = "Trainingset/18.jpg"
    display_image_color_spectrums(image_path)
