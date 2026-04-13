import cv2 as cv
import numpy as np
from PIL import Image

from PIL import Image

def detect_crowns(search_image, templates, search_thresh1, search_thresh2, template_thresh1, template_thresh2):
    """
    Detects crowns using template matching and verifies with Canny edge comparison.
    """
    potential_matches = []
    template_matching_threshold = 0.7  # Initial threshold for finding potential crowns

    # --- Step 1: Initial Template Matching ---
    for original_template in templates:
        if original_template is None:
            continue

        for scale in np.linspace(0.8, 0.2, 25):
            resized_w = int(original_template.shape[1] * scale)
            resized_h = int(original_template.shape[0] * scale)
            if resized_w < 15 or resized_h < 15:
                continue
            
            resized_t = cv.resize(original_template, (resized_w, resized_h))
            
            for angle in [0, 90, 180, 270]:
                if angle == 0:
                    curr_t = resized_t
                elif angle == 90:
                    curr_t = cv.rotate(resized_t, cv.ROTATE_90_CLOCKWISE)
                elif angle == 180:
                    curr_t = cv.rotate(resized_t, cv.ROTATE_180)
                elif angle == 270:
                    curr_t = cv.rotate(resized_t, cv.ROTATE_90_COUNTERCLOCKWISE)
                
                # Match on the original grayscale images
                res = cv.matchTemplate(search_image, curr_t, cv.TM_CCOEFF_NORMED)
                loc = np.where(res >= template_matching_threshold)
                
                h, w = curr_t.shape
                for pt in zip(*loc[::-1]):
                    # Store the potential match rectangle and the template used
                    potential_matches.append(([int(pt[0]), int(pt[1]), int(w), int(h)], curr_t))

    # --- Step 2: Verification with Canny Edge Matching ---
    confirmed_rects = []
    edge_similarity_threshold = 0.2  # Threshold for the edge comparison step

    search_edges = cv.Canny(search_image, search_thresh1, search_thresh2)

    for rect, template in potential_matches:
        x, y, w, h = rect
        
        # Get the region of interest (ROI) from the search image's edges
        roi_edges = search_edges[y:y+h, x:x+w]
        
        # Get the edges of the template that made the match
        template_edges = cv.Canny(template, template_thresh1, template_thresh2)
        
        # Ensure template_edges is not larger than roi_edges
        if template_edges.shape[0] > roi_edges.shape[0] or template_edges.shape[1] > roi_edges.shape[1]:
            continue

        # Compare the ROI edges with the template edges
        edge_res = cv.matchTemplate(roi_edges, template_edges, cv.TM_CCOEFF_NORMED)
        
        # If the edges are a good match, confirm the detection
        if np.max(edge_res) >= edge_similarity_threshold:
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

def main():
    # 1. SETUP
    main_path = r"C:\Users\danie\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\Trainingset\7.jpg"
    template_paths = [
        r"C:\Users\danie\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\features\Kongekrone.png"]

    # Canny edge detection thresholds for the search image
    search_thresh1 = 150
    search_thresh2 = 180

    # Canny edge detection thresholds for the templates
    template_thresh1 = 185
    template_thresh2 = 200

    img_bgr = cv.imread(main_path)
    if img_bgr is None: raise FileNotFoundError("Image not found")
    search_image = cv.split(img_bgr)[0] 

    templates = [cv.imread(path, cv.IMREAD_GRAYSCALE) for path in template_paths]

    # --- Visualization ---
    cv.imshow("Original Image", img_bgr)
    cv.imshow("Grayscale Search Image", search_image)

    # Show Canny edges for search image
    search_edges = cv.Canny(search_image, search_thresh1, search_thresh2)
    cv.imshow("Search Image Edges", search_edges)

    # Show Canny edges for the first template for comparison
    if templates and templates[0] is not None:
        template_edges = cv.Canny(templates[0], template_thresh1, template_thresh2)
        cv.imshow("Template Edges", template_edges)
    
    cv.waitKey(0) # Wait for a key press to continue

    print("Scanning for all crowns...")

    # 2. THE SEARCH
    rects = detect_crowns(search_image, templates, search_thresh1, search_thresh2, template_thresh1, template_thresh2)

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