import random
import td

# --- SCRIPT PARAMETERS ---
my_words = ["attention", "is", "all", "you",
            "need", "to", "create", "dynamic", "typography"]
container_w = 1920
container_h = 1080
padding = 25

# --- FONT PARAMETERS ---
FONT_NAME = "Bahnschrift"
FONT_TYPEFACE = "Regular"
FONT_SIZE = 130

# --- NODE LAYOUT PARAMETERS ---
NODE_SPACE_X = 200
NODE_SPACE_Y = 150

# --- HELPER FUNCTIONS ---


def get_word_dimensions(word_string, base_op):
    """
    Uses a temporary Text TOP and Info CHOP to get the precise pixel
    dimensions of a rendered word.
    """
    if not base_op:
        print("ERROR: Base component not found in get_word_dimensions.")
        return 0, 0

    text_top = base_op.op('temp_text') or base_op.create(
        td.textTOP, "temp_text")
    text_top.par.text = word_string
    text_top.par.font = FONT_NAME
    text_top.par.typeface = FONT_TYPEFACE
    text_top.par.fontsizex = FONT_SIZE

    # The resolution here just needs to be large enough not to clip the text
    text_top.par.resolutionw = container_w
    text_top.par.resolutionh = container_h

    info_chop = base_op.op('temp_info') or base_op.create(
        td.infoCHOP, "temp_info")
    info_chop.par.op = text_top
    info_chop.cook(force=True)  # Ensure the CHOP has the latest values

    width = float(info_chop['text_width'])
    height = float(info_chop['text_height'])

    return width, height

# --- LOGIC & CALCULATION ---


def pack_words_generatively(words_to_pack, container_width, container_height, padding, base_op):
    """
    Calculates the position and rotation for each word to fit inside a container.
    This function DOES NOT create any TouchDesigner nodes.
    It returns a list of placement data.
    """
    layout_data = []

    # Shelf state initialization (origin is top-left)
    shelf_x = 0
    shelf_y = 0
    shelf_height = 0

    words_queue = list(words_to_pack)

    while words_queue:
        word = words_queue[0]
        original_width, original_height = get_word_dimensions(word, base_op)

        # Dimensions for horizontal and vertical placement, including padding
        h_width = original_width + padding
        h_height = original_height + padding
        v_width = original_height + padding
        v_height = original_width + padding

        # Check if either orientation can fit on the current shelf
        can_fit_horizontally = (shelf_x + h_width) <= container_width
        can_fit_vertically = (shelf_x + v_width) <= container_width

        placed_on_current_shelf = False

        # Determine which orientation to use
        chosen_rotation = 0
        if can_fit_horizontally and can_fit_vertically:
            chosen_rotation = 0 if random.choice([True, False]) else 90
            placed_on_current_shelf = True
        elif can_fit_horizontally:
            chosen_rotation = 0
            placed_on_current_shelf = True
        elif can_fit_vertically:
            chosen_rotation = 90
            placed_on_current_shelf = True

        if placed_on_current_shelf:
            # Calculate word's center based on its top-left corner and dimensions
            if chosen_rotation == 0:
                center_x = shelf_x + (original_width / 2)
                center_y = shelf_y + (original_height / 2)
                shelf_x += h_width
                shelf_height = max(shelf_height, h_height)
            else:  # rotation is 90
                center_x = shelf_x + (original_height / 2)
                center_y = shelf_y + (original_width / 2)
                shelf_x += v_width
                shelf_height = max(shelf_height, v_height)

            layout_data.append({
                'word': word,
                'x': center_x,
                'y': center_y,
                'width': original_width,
                'height': original_height,
                'rotation': chosen_rotation
            })
            words_queue.pop(0)
        else:
            # Word doesn't fit, try to start a new shelf
            new_shelf_y = shelf_y + shelf_height

            # Check if the word can fit on a new shelf in *at least one* orientation
            can_start_new_shelf_h = (
                new_shelf_y + h_height) <= container_height and h_width <= container_width
            can_start_new_shelf_v = (
                new_shelf_y + v_height) <= container_height and v_width <= container_width

            if can_start_new_shelf_h or can_start_new_shelf_v:
                shelf_y = new_shelf_y
                shelf_x = 0
                shelf_height = 0
                # The loop will continue and retry the word on the next iteration
            else:
                # Word truly cannot fit.
                print(
                    f"Warning: Word '{word}' cannot fit. Container is full. Skipping.")
                words_queue.pop(0)

    return layout_data

# --- TOUCHDESIGNER NODE CREATION ---


def create_layout_from_data(layout_data, container_width, container_height, base_op):
    """
    Takes a list of placement data and builds the TouchDesigner network.
    """
    if not base_op:
        print("ERROR: Base component 'base1' not found.")
        return

    transform_tops = []

    for i, data in enumerate(layout_data):
        word_string = data['word']
        rotation = data['rotation']
        word_w = data['width']
        word_h = data['height']

        # --- Coordinate Conversion ---
        final_tx = data['x'] - (container_width / 2)
        final_ty = (container_height / 2) - data['y']

        # Create the Text TOP for the word
        text_top = base_op.create(td.textTOP, f"text{i}")
        text_top.nodeX = 0
        text_top.nodeY = -NODE_SPACE_Y * i
        text_top.viewer = True
        text_top.par.text = word_string
        text_top.par.font = FONT_NAME
        text_top.par.typeface = FONT_TYPEFACE
        text_top.par.fontsizex = FONT_SIZE

        # --- CRITICAL FIX: Set resolution to match the text content ---
        # This ensures the rotation pivot is the center of the word.
        text_top.par.resolutionw = word_w
        text_top.par.resolutionh = word_h

        # Create a Transform TOP to position and rotate the word
        transform_top = base_op.create(td.transformTOP, f"transform{i}")
        transform_top.nodeX = NODE_SPACE_X
        transform_top.nodeY = -NODE_SPACE_Y * i
        transform_top.viewer = True
        transform_top.setInputs([text_top])

        # Set the final, converted position and rotation
        transform_top.par.tx = final_tx
        transform_top.par.ty = final_ty
        transform_top.par.tunit = 0  # Set Translate Units to Pixels
        transform_top.par.rotate = rotation

        transform_tops.append(transform_top)

    # Composite all the transformed text TOPs together
    comp = base_op.create(td.compositeTOP, "comp1")
    comp.nodeX = NODE_SPACE_X * 2
    comp.viewer = True
    comp.par.resolutionw = container_w
    comp.par.resolutionh = container_h
    comp.par.operand = 'add'
    comp.setInputs(transform_tops)

    # Create a final Out TOP
    out = base_op.create(td.outTOP, "out1")
    out.nodeX = NODE_SPACE_X * 3
    out.viewer = True
    out.par.resolutionw = container_w
    out.par.resolutionh = container_h
    out.setInputs([comp])


# --------
# EXECUTION
# --------
def run():
    """
    Main execution function to run the entire process.
    """
    print("Starting layout process...")

    # Ensure a clean slate
    base = op('base1')
    if base:
        base.destroy()

    base = me.parent().create(baseCOMP, "base1")

    # 1. Calculate the layout
    print("Calculating word positions...")
    layout = pack_words_generatively(
        my_words, container_w, container_h, padding, base)

    # 2. Build the TouchDesigner network from the calculated data
    print("Creating TouchDesigner nodes...")
    create_layout_from_data(layout, container_w, container_h, base)

    # Clean up temporary nodes
    if base.op('temp_text'):
        base.op('temp_text').destroy()
    if base.op('temp_info'):
        base.op('temp_info').destroy()

    print("\n--- Layout Calculation Complete ---")
    for item in layout:
        print(
            f"Word: '{item['word']}', Center: ({item['x']:.1f}, {item['y']:.1f}), Rot: {item['rotation']} deg")

    print("\nScript finished.")


# To run this, execute the run() function from a Text DAT.
run()
