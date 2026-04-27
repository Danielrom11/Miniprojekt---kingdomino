import os
import cv2 as cv
import numpy as np

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

def build_crown_templates(features_dir, template_count=18):
    """
    Loads konge_krone_1..N templates and attaches shared thresholds used by
    template matching and Canny edge verification.
    """
    template_thresh1 = 140
    template_thresh2 = 180
    match_threshold = 0.65
    edge_sim_threshold = 0.15

    templates_with_thresholds = []
    for idx in range(1, template_count + 1):
        template_path = os.path.join(features_dir, f"konge_krone_{idx}.JPG")
        if not os.path.isfile(template_path):
            # Fallback if extension casing differs on disk
            template_path = os.path.join(features_dir, f"konge_krone_{idx}.jpg")

        template_hsv, template_hsv_gray = load_and_prepare_template(template_path)
        if template_hsv is None or template_hsv_gray is None:
            continue

        templates_with_thresholds.append(
            (
                template_hsv,
                template_hsv_gray,
                template_thresh1,
                template_thresh2,
                match_threshold,
                edge_sim_threshold,
            )
        )

    print(f"Loaded {len(templates_with_thresholds)} crown templates for matching.")
    return templates_with_thresholds

def main():
    # 1. SETUP
    main_path = r"G:\Andre computere\My laptop\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\Trainingset\43.jpg"
    
    # Pre-load all konge_krone templates (1..18) used by template matching and Canny verification
    features_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "features")
    templates_with_thresholds = build_crown_templates(features_dir, template_count=18)
    if not templates_with_thresholds:
        print("No crown templates were loaded. Check the files in features/.")
        return

    # Canny edge detection thresholds for the search image
    search_thresh1 = 200
    search_thresh2 = 220

    img_bgr = cv.imread(main_path)
    if img_bgr is None: raise FileNotFoundError("Image not found")
    
    # Convert search image to HSV
    img_hsv = cv.cvtColor(img_bgr, cv.COLOR_BGR2HSV)
    
    # Create a grayscale representation of the raw HSV matrix
    # (treats H as Blue, S as Green, V as Red to flatten them into 1 channel)
    img_hsv_gray = cv.cvtColor(img_hsv, cv.COLOR_BGR2GRAY)
    
    # We are currently using full HSV for template match, and HSV grayscale for edge tests
    search_image_match = img_hsv
    search_image_edges = img_hsv_gray

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