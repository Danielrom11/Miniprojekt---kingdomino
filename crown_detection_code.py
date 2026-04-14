import cv2 as cv
import numpy as np
from PIL import Image

from PIL import Image

def detect_crowns(search_image_match, search_image_edges, templates_with_thresholds, search_thresh1, search_thresh2):
    """
    Detects crowns using template matching and verifies with Canny edge comparison.
    """
    potential_matches = []

    # --- Step 1: Initial Template Matching ---
    for template_data in templates_with_thresholds:
        template_hsv, template_hsv_gray, t_thresh1, t_thresh2, match_thresh, edge_sim_thresh = template_data
        if template_hsv is None:
            continue

        # A 90x130 template in a 500x500 board means the crown is HUGE in the template.
        # Let's scale down further. If a crown is 20x20 pixels on the 100x100 tile,
        # we need the scale to reach down to ~0.15 (13x19 pixels) or 0.2 (18x26 pixels).
        for scale in np.linspace(1.15, 0.95, 5):
            resized_w = int(template_hsv.shape[1] * scale)
            resized_h = int(template_hsv.shape[0] * scale)
            if resized_w < 15 or resized_h < 15:
                continue
            
            resized_t_hsv = cv.resize(template_hsv, (resized_w, resized_h))
            resized_t_gray = cv.resize(template_hsv_gray, (resized_w, resized_h))
            
            for angle in [0, 90, 180, 270]:
                if angle == 0:
                    curr_t_hsv = resized_t_hsv
                    curr_t_gray = resized_t_gray
                elif angle == 90:
                    curr_t_hsv = cv.rotate(resized_t_hsv, cv.ROTATE_90_CLOCKWISE)
                    curr_t_gray = cv.rotate(resized_t_gray, cv.ROTATE_90_CLOCKWISE)
                elif angle == 180:
                    curr_t_hsv = cv.rotate(resized_t_hsv, cv.ROTATE_180)
                    curr_t_gray = cv.rotate(resized_t_gray, cv.ROTATE_180)
                elif angle == 270:
                    curr_t_hsv = cv.rotate(resized_t_hsv, cv.ROTATE_90_COUNTERCLOCKWISE)
                    curr_t_gray = cv.rotate(resized_t_gray, cv.ROTATE_90_COUNTERCLOCKWISE)
                
                # Match on the HSV images
                res = cv.matchTemplate(search_image_match, curr_t_hsv, cv.TM_CCOEFF_NORMED)
                loc = np.where(res >= match_thresh)
                
                h, w = curr_t_gray.shape[:2]
                for pt in zip(*loc[::-1]):
                    # Store the potential match rectangle, the *gray* template used, and its specific thresholds
                    potential_matches.append(([int(pt[0]), int(pt[1]), int(w), int(h)], curr_t_gray, t_thresh1, t_thresh2, edge_sim_thresh))

    # --- Step 2: Verification with Canny Edge Matching ---
    confirmed_rects = []

    search_edges = cv.Canny(search_image_edges, search_thresh1, search_thresh2)

    for rect, template_gray, t_thresh1, t_thresh2, edge_sim_thresh in potential_matches:
        x, y, w, h = rect
        
        # Get the region of interest (ROI) from the search image's edges
        roi_edges = search_edges[y:y+h, x:x+w]
        
        # Get the edges of the template that made the match
        template_edges = cv.Canny(template_gray, t_thresh1, t_thresh2)
        
        # Ensure template_edges is not larger than roi_edges
        if template_edges.shape[0] > roi_edges.shape[0] or template_edges.shape[1] > roi_edges.shape[1]:
            continue

        # Compare the ROI edges with the template edges
        edge_res = cv.matchTemplate(roi_edges, template_edges, cv.TM_CCOEFF_NORMED)
        
        # If the edges are a good match, confirm the detection
        if np.max(edge_res) >= edge_sim_thresh:
            confirmed_rects.append(rect)

    # Group the confirmed rectangles to merge overlapping boxes
    rects, _ = cv.groupRectangles(confirmed_rects, groupThreshold=1, eps=0.5)
    
    return rects

def overlay_images(background_path, foreground_path, output_path):
    """
    Overlays a PNG image with a transparent background onto a JPG image.

    Args:
        background_path (str): The path to the background JPG image.
        foreground_path (str): The path to the foreground PNG image.
        output_path (str): The path to save the resulting image.
    """
    try:
        # Open the background and foreground images
        background = Image.open(background_path).convert("RGBA")
        foreground = Image.open(foreground_path).convert("RGBA")

        # Paste the foreground onto the background using the alpha channel as a mask
        background.paste(foreground, (0, 0), foreground)

        # Save the resulting image
        background.save(output_path, "PNG")
        print(f"Image saved to {output_path}")

    except FileNotFoundError as e:
        print(f"Error: {e}. Please check the file paths.")
    except Exception as e:
        print(f"An error occurred: {e}")

def load_and_prepare_template(path):
    """
    Loads a color template, converts to HSV, and returns both the full HSV and the HSV grayscale.
    """
    img_bgr = cv.imread(path, cv.IMREAD_COLOR)
    if img_bgr is None:
        print(f"Warning: Could not load template at {path}")
        return None, None
    
    # Convert the image to HSV color space
    img_hsv = cv.cvtColor(img_bgr, cv.COLOR_BGR2HSV)
    
    # Create a grayscale representation of the raw HSV matrix for Canny edges
    img_hsv_gray = cv.cvtColor(img_hsv, cv.COLOR_BGR2GRAY)
    return img_hsv, img_hsv_gray

def main():
    # 1. SETUP
    main_path = r"C:\Users\danie\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\Trainingset\59.jpg"
    
    # Pre-load crown templates with their specific thresholds
    # Format: (img_hsv, img_v, template_thresh1, template_thresh2, match_threshold, edge_sim_threshold)
    templates_with_thresholds = [
        (*load_and_prepare_template(r"C:\Users\danie\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\features\krone_blaa_baggrund_hr.jpg"), 180, 210, 0.7, 0.15),
        (*load_and_prepare_template(r"C:\Users\danie\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\features\krone_blaa_baggrund_lr.jpg"), 130, 150, 0.7, 0.15),
        (*load_and_prepare_template(r"C:\Users\danie\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\features\krone_sort_baggrund_hr.jpg"), 140, 180, 0.6, 0.15),
        (*load_and_prepare_template(r"C:\Users\danie\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\features\krone_sort_baggrund_lr.jpg"), 80, 110, 0.6, 0.15),
        (*load_and_prepare_template(r"C:\Users\danie\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\features\krone_sort_baggrund.jpg"), 140, 180, 0.6, 0.15)
    ]

    # Canny edge detection thresholds for the search image
    search_thresh1 = 200
    search_thresh2 = 220

    img_bgr = cv.imread(main_path)
    if img_bgr is None: raise FileNotFoundError("Image not found")
    
    # Convert search image to HSV and extract channels
    img_hsv = cv.cvtColor(img_bgr, cv.COLOR_BGR2HSV)
    h_channel, s_channel, v_channel = cv.split(img_hsv)
    
    # Create a grayscale representation of the raw HSV matrix
    # (treats H as Blue, S as Green, V as Red to flatten them into 1 channel)
    img_hsv_gray = cv.cvtColor(img_hsv, cv.COLOR_BGR2GRAY)
    
    # We are currently using full HSV for template match, and HSV grayscale for edge tests
    search_image_match = img_hsv
    search_image_edges = img_hsv_gray

    # --- Visualization ---
    cv.imshow("Original Image", img_bgr)
    cv.imshow("HSV Grayscale", img_hsv_gray)
    cv.imshow("Full HSV Image", img_hsv)
    cv.imshow("HSV: Hue Channel", h_channel)
    cv.imshow("HSV: Saturation Channel", s_channel)
    cv.imshow("HSV: Value Channel", v_channel)

    # Show Canny edges for search image
    search_edges = cv.Canny(search_image_edges, search_thresh1, search_thresh2)
    cv.imshow("Search Image Edges", search_edges)

    # Show Canny edges for all templates for comparison
    for i, template_data in enumerate(templates_with_thresholds):
        _, template_hsv_gray, t_thresh1, t_thresh2, _, _ = template_data
        if template_hsv_gray is not None:
            template_edges = cv.Canny(template_hsv_gray, t_thresh1, t_thresh2)
            cv.imshow(f"Template {i+1} Edges", template_edges)
    
    cv.waitKey(0) # Wait for a key press to continue

    print("Scanning for all crowns...")

    # 2. THE SEARCH
    rects = detect_crowns(search_image_match, search_image_edges, templates_with_thresholds, search_thresh1, search_thresh2)

    # 4. DRAW
    result_img = img_bgr.copy()
    for (x, y, w, h) in rects:
        cv.rectangle(result_img, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv.putText(result_img, "Crown", (x, y - 10), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    print(f"Success! Found {len(rects)} crowns.")

    cv.namedWindow("Result", cv.WINDOW_NORMAL)
    cv.imshow("Result", result_img)
    cv.waitKey(0)
    cv.destroyAllWindows()

if __name__ == "__main__":
    main()