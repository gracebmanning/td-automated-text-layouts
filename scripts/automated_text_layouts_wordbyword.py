import sys
# This allows the script to find your custom find_transcript_groupings.py file
# Ensure the path is correct for your project structure.
sys.path.extend(
    ["C:/Projects/td-automated-text-layouts/scripts"])
from helpers.find_transcript_groupings import find_grouping_times  # nopep8

# -----------------
# USER PARAMETERS
# -----------------
# File paths for the transcript and word groupings
transcript_filename = "../input_files/attentionIsAllYouNeed1_transcript.json"
groupings_filename = "../input_files/attentionIsAllYouNeed1_groupings.txt"

# Font styling
font_name = "Bahnschrift"
font_typeface = "Regular"
font_size = 130

# The maximum number of characters allowed on a single line of text.
# The user must determine this value based on the chosen font and font size.
MAX_CHARS_PER_LINE = 12

# node layout spacing
NODES_PER_ROW = 4
BASE_SPACING = 200
TOP_SPACING_X = 200
TOP_SPACING_Y = 100

# Set to False to disable word-level reveals.
ENABLE_WORD_BY_WORD_ANIMATION = False


# Script assumes it is running from within the target parent container.
parent = me.parent()
FPS = project.cookRate  # FPS of the project
LAST_FRAME = me.time.end  # Last frame of the project

# -----------------
# SCRIPT LOGIC
# -----------------


def create_text_layouts():
    """
    Reads a groupings file and creates a Base COMP with Text and Layout TOPs
    for each line. 
    """
    # Open the word groupings file and process each line
    with open(groupings_filename, 'r') as f:
        group_lines = f.readlines()

    for i, line in enumerate(group_lines):
        line = line.strip()  # Remove any leading/trailing whitespace
        if not line:
            continue

        animation_x = 0  # stays the same
        animation_y = 0  # increment by TOP_SPACING_Y * 2 for each group

        null_x = TOP_SPACING_X  # stay the same
        # increment by TOP_SPACING for each word, increment by TOP_SPACING * 2 for each group
        null_y = animation_y

        word_x = TOP_SPACING_X*2  # stay the same
        # increment by TOP_SPACING for each word, increment by TOP_SPACING * 2 for each group
        word_y = animation_y

        line_layout_x = TOP_SPACING_X*3  # stay the same
        line_layout_y = 0  # increment by TOP_SPACING * 2 for each group

        final_layout_x = TOP_SPACING_X*4
        final_layout_y = -TOP_SPACING_Y

        out_x = TOP_SPACING_X*5
        out_y = -TOP_SPACING_Y

        # --- Create a Base COMP for the group ---
        base = parent.create(baseCOMP, f"group{i}")
        base.viewer = True
        row = i // NODES_PER_ROW
        col = i % NODES_PER_ROW
        base.nodeX = col * BASE_SPACING
        base.nodeY = row * -BASE_SPACING  # build downwards

        # --- Process the line to fit words within max_chars_per_line ---
        words = line.split()
        processed_lines = []
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 > MAX_CHARS_PER_LINE:
                processed_lines.append(current_line)
                current_line = word
            else:
                current_line += f" {word}" if current_line else word
        processed_lines.append(current_line)

        # --- Create Internal Network for each line ---
        all_layout_tops = []

        for j, text_line in enumerate(processed_lines):
            words_in_line = text_line.split()
            if not words_in_line:
                continue

            # A layout for each line to arrange words horizontally
            line_layout = base.create(layoutTOP, f"line_layout{j}")
            line_layout.viewer = True
            line_layout.par.scaleres = 1  # Scale Resolution to Fit
            line_layout.par.align = 1  # Left to Right
            line_layout.par.fit = 3       # Fit: Fit Best
            line_layout.par.resolutionw = parent.par.w
            line_layout.par.resolutionh = parent.par.h / len(processed_lines)
            line_layout.nodeX = line_layout_x
            line_layout.nodeY = line_layout_y
            all_layout_tops.append(line_layout)

            # Create ONE animation COMP per line of text if enabled
            line_anim = None
            if ENABLE_WORD_BY_WORD_ANIMATION:
                line_anim = base.create(animationCOMP, f"line_anim{j}")
                line_anim.nodeX = animation_x
                line_anim.nodeY = animation_y
                channels_dat = line_anim.op('channels')
                channels_dat.clear(keepFirstRow=True)

            word_tops_for_line_layout = []

            # Create a separate Text TOP for each word
            for k, word in enumerate(words_in_line):
                # Add a space for layout, except for the last word
                display_text = word if k == len(
                    words_in_line) - 1 else f"{word} "

                word_top = base.create(textTOP, f"word_{j}_{k}")
                word_top.viewer = True
                word_top.par.text = display_text
                word_top.par.font = font_name
                word_top.par.typeface = font_typeface
                word_top.par.fontsizex = font_size
                word_top.par.alignx = 'left'
                word_top.par.resolutionw = parent.par.w / len(words_in_line)
                word_top.par.resolutionh = parent.par.h / len(processed_lines)
                word_top.nodeX = word_x
                word_top.nodeY = word_y
                word_tops_for_line_layout.append(word_top)

                if ENABLE_WORD_BY_WORD_ANIMATION and line_anim:
                    channel_name = f"word{k}_alpha"
                    channels_dat.appendRow(
                        [channel_name, 1, 'hold', 'hold', 0, 'keys', 0.3, 0.14, 0.7, 0, 0, 0])
                    line_anim_null = base.create(nullCHOP, f"word{k}_null")
                    line_anim_null.viewer = True
                    line_anim_null.nodeX = null_x
                    line_anim_null.nodeY = null_y
                    line_anim_null.inputConnectors[0].connect(
                        line_anim.outputConnectors[0])
                    word_top.par.fontalpha.expr = f"op('{line_anim_null.name}')['{channel_name}']"
                else:
                    word_top.par.fontalpha = 1  # Make sure word is visible if not animating

                word_y -= TOP_SPACING_Y
                null_y -= TOP_SPACING_Y

            line_layout.setInputs(word_tops_for_line_layout)

            animation_y -= TOP_SPACING_Y * 2
            # null_y -= TOP_SPACING_Y
            # word_y -= TOP_SPACING_Y
            line_layout_y -= TOP_SPACING_Y * 2

        # --- Create Final Layout in Base to stack the lines vertically ---
        final_layout = base.create(layoutTOP, "final_layout")
        final_layout.viewer = True
        final_layout.par.scaleres = 1  # Scale Resolution to Fit
        final_layout.par.align = 3  # Top to Bottom
        final_layout.par.fit = 3    # Fit: Fit Best
        final_layout.setInputs(all_layout_tops)
        final_layout.par.resolutionw = parent.par.w
        final_layout.par.resolutionh = parent.par.h
        final_layout.nodeX = final_layout_x
        final_layout.nodeY = final_layout_y

        out = base.create(outTOP, "out1")
        out.viewer = True
        out.setInputs([final_layout])
        out.nodeX = out_x
        out.nodeY = out_y


def setup_animation():
    """
    Finds all 'group*' COMPs and connects them to a main Switch TOP using
    connectors. It then creates an Animation COMP to drive the switch.
    """
    # 1. Find all 'group' Base COMPs that were created in the parent.
    all_groups = parent.findChildren(type=baseCOMP, name="group*")

    if not all_groups:
        print("No 'group' components found to connect.")
        return

    # Correctly position the switch to the right of the vertical stack of groups
    node_x_start = (NODES_PER_ROW * BASE_SPACING) + 100

    # 2. Create the main Switch TOP
    main_switch = parent.create(switchTOP, "mainSwitch")
    main_switch.viewer = True
    main_switch.nodeX = node_x_start

    # --- NEW CONNECTION LOGIC ---
    # Loop through each Base COMP and explicitly connect its first output
    # to the corresponding input on the Switch TOP.
    for i, group_comp in enumerate(all_groups):
        main_switch.inputConnectors[i].connect(group_comp.outputConnectors[0])

    # 3. Set up the Animation COMP to drive the switch
    anim = parent.create(animationCOMP, "mainAnimation")
    node_x_start += BASE_SPACING
    anim.nodeX = node_x_start

    # Configure the 'index' channel in the Animation COMP's CHOP data
    channels_dat = anim.op('channels')
    channels_dat.clear(keepFirstRow=True)
    channels_dat.appendRow(
        ['index', 1, 'hold', 'hold', 0, 'keys', 0.3, 0.14, 0.7, 0, 0, 0])

    # 4. Create a Null CHOP to hold the index channel value
    index_out = parent.create(nullCHOP, "index_out")
    index_out.viewer = True
    node_x_start += BASE_SPACING
    index_out.nodeX = node_x_start
    index_out.inputConnectors[0].connect(anim.outputConnectors[0])

    # Connect the animation to the Switch TOP's index parameter
    main_switch.par.index.expr = f"op('{index_out.name}')['index']"


def create_animations():
    """
    Parses the transcript to create all keyframe animations. The word-by-word
    animation is only created if ENABLE_WORD_BY_WORD_ANIMATION is True.
    """
    matched_group_timings = find_grouping_times(groupings_filename, transcript_filename)  # nopep8

    # --- Populate the Main Animation for Group Switching ---
    anim = op('mainAnimation')
    keys_dat = anim.op('keys')
    keys_dat.clear(keepFirstRow=True)
    keys_dat.appendRow([1, 1, 0, 0, 0, "constant()", 0, 0]
                       )  # Append first row at Frame 1
    # Loop through groupings and add rows to keys DAT
    for i, item in enumerate(matched_group_timings):
        start_frame = item["start_time"] * FPS
        keys_dat.appendRow([1, start_frame, i, 0, 0, "constant()", 0, 0])
    # Append last row at last_frame
    keys_dat.appendRow([1, LAST_FRAME, 0, 0, 0, "constant()", 0, 0])

    # --- 2. Populate Word-Level Animations (Conditional) ---
    if not ENABLE_WORD_BY_WORD_ANIMATION:
        print("Skipping word-by-word animation creation.")
        return
    for i, group_data in enumerate(matched_group_timings):
        group_comp = parent.op(f"group{i}")
        if not group_comp:
            continue

        text_tops = group_comp.findChildren(type=textTOP, name="text*")
        for text_top in text_tops:
            line_text = text_top.par.text.eval()
            anim_op_name = text_top.name.replace("text", "word_anim")
            word_anim = group_comp.op(anim_op_name)
            if not word_anim:
                continue

            words_for_line = find_words_for_line(line_text, group_data)
            num_words = len(words_for_line)
            if num_words == 0:
                continue

            word_keys_dat = word_anim.op('keys')
            word_keys_dat.clear(keepFirstRow=True)
            word_keys_dat.appendRow([1, 1, 0, 0, 0, "constant()", 0, 0])
            for j, word_info in enumerate(words_for_line):
                start_frame = word_info['start_time'] * FPS
                phase_value = (j + 1) / num_words
                word_keys_dat.appendRow(
                    [1, start_frame, phase_value, 0, 0, "constant()", 0, 0])


# -----------------
# EXECUTION
# -----------------
# Clear previous components if they exist to allow for rerunning the script
print("Clearing old components...")
old_components = []
old_components.extend(parent.findChildren(name="group*"))
old_components.extend(parent.findChildren(name="mainSwitch"))
old_components.extend(parent.findChildren(name="mainAnimation"))
old_components.extend(parent.findChildren(name="index_out"))
for op_object in old_components:
    op_object.destroy()

# Run the main functions
print("Creating text layouts...")
create_text_layouts()

print("Setting up main animation switch...")
setup_animation()

print("Loading transcript into animation...")
create_animations()

print("Script finished.")
