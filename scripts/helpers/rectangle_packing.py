import random
import td

my_words = ["attention", "is", "all", "you", "need"]
container_w = 1920
container_h = 1080

FONT_NAME = "Bahnschrift"
FONT_TYPEFACE = "Regular"
FONT_SIZE = 130


def get_word_dimensions(word_string):
    """
    1. Create a temporary Text TOP.
    2. Set its 'text' parameter to word_string.
    3. Use an Info CHOP to get the 'text_width' and 'text_height'.
    """
    text_top = me.parent().create(td.textTOP, "temp_text")
    text_top.par.text = word_string
    text_top.par.font = FONT_NAME
    text_top.par.typeface = FONT_TYPEFACE
    text_top.par.fontsizex = FONT_SIZE
    text_top.par.resolutionw = container_w
    text_top.par.resolutionh = container_h

    info_chop = me.parent().create(td.infoCHOP, "temp_info")
    info_chop.par.op = text_top.name
    width = float(info_chop['text_width'])
    height = float(info_chop['text_height'])

    text_top.destroy()
    info_chop.destroy()

    return width, height


def create_text_top(word_string, shelf_x, shelf_y, rotation):
    text_top = me.parent().create(td.textTOP, "text")
    text_top.viewer = True
    text_top.par.text = word_string
    text_top.par.font = FONT_NAME
    text_top.par.typeface = FONT_TYPEFACE
    text_top.par.fontsizex = FONT_SIZE
    text_top.par.resolutionw = container_w
    text_top.par.resolutionh = container_h

    # set position
    text_top.par.positionx = shelf_x
    text_top.par.positiony = shelf_y

    # set rotation
    if (rotation == 90):
        # switch resolution width and height
        text_top.par.resolutionw = container_h
        text_top.par.resolutionh = container_w

        # pass through flip TOP
        flip_top = me.parent().create(td.flipTOP, "flip")
        flip_top.setInputs([text_top])
        flip_top.par.flipy = 1
        flip_top.par.flop = 1

        return flip_top
    else:
        return text_top


def pack_words_generatively(words_to_pack, container_width, container_height, padding=10):
    """
    Arranges a list of words into a container, allowing for 90-degree rotation,
    random orientation choices, and padding.

    Args:
        words_to_pack (list): A list of strings to be placed.
        container_width (int): The width of the target container.
        container_height (int): The height of the target container.
        padding (int): The space to add around each word.

    Returns:
        list: A list of dictionaries, each containing the word, its calculated
              position (x, y), and rotation (0 or 90).
    """
    placed_words = []
    text_tops = []

    # --- Shelf State Initialization ---
    shelf_x = 0
    shelf_y = 0
    shelf_height = 0

    # Use a copy of the list so we can remove words as they are placed
    words_queue = list(words_to_pack)

    while words_queue:
        word = words_queue[0]  # Peek at the next word

        # Get word dimensions
        original_width, original_height = get_word_dimensions(word)

        # Dimensions for horizontal placement
        h_width = original_width + padding
        h_height = original_height + padding

        # Dimensions for vertical placement (swapped)
        v_width = original_height + padding
        v_height = original_width + padding

        # --- Check if either orientation can fit on the current shelf ---
        can_fit_horizontally = (shelf_x + h_width) <= container_width
        can_fit_vertically = (shelf_x + v_width) <= container_width

        # --- Placement Decision Logic ---
        placed_on_current_shelf = False

        # Case 1: Both orientations fit, choose one randomly
        if can_fit_horizontally and can_fit_vertically:
            if random.choice([True, False]):
                placed_words.append(
                    {'word': word, 'x': shelf_x, 'y': shelf_y, 'rotation': 0})
                text_tops.append(create_text_top(word, shelf_x, shelf_y, 0))
                shelf_x += h_width
                shelf_height = max(shelf_height, h_height)
            else:
                placed_words.append(
                    {'word': word, 'x': shelf_x, 'y': shelf_y, 'rotation': 90})
                text_tops.append(create_text_top(word, shelf_x, shelf_y, 90))
                shelf_x += v_width
                shelf_height = max(shelf_height, v_height)
            placed_on_current_shelf = True

        # Case 2: Only horizontal fits
        elif can_fit_horizontally:
            placed_words.append(
                {'word': word, 'x': shelf_x, 'y': shelf_y, 'rotation': 0})
            text_tops.append(create_text_top(word, shelf_x, shelf_y, 0))
            shelf_x += h_width
            shelf_height = max(shelf_height, h_height)
            placed_on_current_shelf = True

        # Case 3: Only vertical fits
        elif can_fit_vertically:
            placed_words.append(
                {'word': word, 'x': shelf_x, 'y': shelf_y, 'rotation': 90})
            text_tops.append(create_text_top(word, shelf_x, shelf_y, 90))
            shelf_x += v_width
            shelf_height = max(shelf_height, v_height)
            placed_on_current_shelf = True

        # --- Shelf Management ---
        if placed_on_current_shelf:
            words_queue.pop(0)  # Successfully placed, remove from queue
        else:
            # Word doesn't fit on the current shelf, try to start a new one.
            new_shelf_y = shelf_y + shelf_height

            # Check if the smallest dimension of the word can fit on a new shelf
            min_new_height = min(h_height, v_height)
            if (new_shelf_y + min_new_height) <= container_height:
                # It's possible to start a new shelf.
                shelf_y = new_shelf_y
                shelf_x = 0
                shelf_height = 0
                # The loop will now retry placing the same word on this new shelf.
            else:
                # Container is full, cannot place this word.
                print(
                    f"Warning: Word '{word}' cannot fit. Container height limit reached. Skipping.")
                # Give up on this word and move to the next.
                words_queue.pop(0)

    return placed_words


# --------
# EXECUTION
# --------
print(my_words)

layout = pack_words_generatively(
    my_words, container_w, container_h, padding=15)

print(f"\n--- Layout for {container_w}x{container_h} container ---")
for item in layout:
    print(
        f"Word: '{item['word']}', Position: ({item['x']}, {item['y']}), Rotation: {item['rotation']} deg")
