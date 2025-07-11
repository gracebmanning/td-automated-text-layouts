import td
import json
import sys
sys.path.extend(
    ["C:/Projects/td-automated-text-layouts/scripts"])
from helpers.find_transcript_groupings import find_grouping_times, find_grouping_times_json  # nopep8
# from helpers.layouts import basic_layout, rectangular_fit_layout  # nopep8

# "animation_style": ["group_basic", "group_rectangular", "group_swirl", "word_basic", "word_impact"]
# "options": ["audioreactive_scale, "invert_colors"]

# -----------------
# USER PARAMETERS
# -----------------
# File paths for the transcript, word groupings, audio
transcript_filename = "../input_files/attentionIsAllYouNeed1_transcript.json"
groupings_filename = "../input_files/attentionIsAllYouNeed1_groupings.json"
audio_filename = "../input_files/attentionIsAllYouNeed1_audio.mp3"

# Font styling
FONT_NAME = "Bahnschrift"
FONT_TYPEFACE = "Regular"
FONT_SIZE = 130

# The maximum number of characters allowed on a single line of text.
# The user must determine this value based on the chosen font and font size.
MAX_CHARS_PER_LINE = 12

# node layout spacing
NODES_PER_ROW = 4
BASE_SPACING = 200
TOP_SPACING = 200

# Script assumes it is running from within the target parent container.
parent = me.parent()
FPS = project.cookRate  # FPS of the project
LAST_FRAME = me.time.end  # Last frame of the

# -----------------
# SCRIPT LOGIC
# -----------------


def import_audio():
    """
    Creates audiofilein CHOP, plus info CHOP, audioAnalysis and audiodevout CHOP.
    """
    # Audio File In
    audio_file = parent.create(td.audiofileinCHOP, "audio_file")
    audio_file.nodeX -= BASE_SPACING * 2
    audio_file.nodeY = 300
    audio_file.viewer = True
    audio_file.par.file = audio_filename
    audio_file.par.playmode = 0

    # Device Out, Audio Info
    audio_out = parent.create(td.audiodeviceoutCHOP, "audio_out")
    audio_out.nodeX -= BASE_SPACING
    audio_out.nodeY = 450
    audio_out.viewer = True
    audio_out.inputConnectors[0].connect(audio_file.outputConnectors[0])
    audio_info = parent.create(td.infoCHOP, "audio_info")
    audio_info.nodeX -= BASE_SPACING
    audio_info.nodeY = 350
    audio_info.viewer = True
    audio_info.setInputs([audio_file])

    # Audioreactive Scale group
    audioreactive_scale = parent.create(td.baseCOMP, "audioreactive_scale")
    audioreactive_scale.nodeX -= BASE_SPACING
    audioreactive_scale.nodeY = 200
    in1 = audioreactive_scale.create(td.inCHOP, "in1")
    in1.viewer = True

    # Math1
    math1 = audioreactive_scale.create(td.mathCHOP, "math1")
    math1.setInputs([in1])
    math1.nodeX = 200
    math1.viewer = True
    math1.par.chanop = 5  # Combine Channels = Average

    # Audio Spectrum
    audiospect1 = audioreactive_scale.create(
        td.audiospectrumCHOP, "audiospect1")
    audiospect1.setInputs([math1])
    audiospect1.nodeX = 400
    audiospect1.viewer = True

    # Analyze
    analyze1 = audioreactive_scale.create(td.analyzeCHOP, "analyze1")
    analyze1.setInputs([audiospect1])
    analyze1.nodeX = 600
    analyze1.viewer = True

    # Math 2
    math2 = audioreactive_scale.create(td.mathCHOP, "math2")
    math2.setInputs([analyze1])
    math2.nodeX = 800
    math2.viewer = True
    math2.par.torange1 = 0.8  # set To Range to (0.8-1)

    # Null / Out
    null1 = audioreactive_scale.create(td.nullCHOP, "null1")
    null1.setInputs([math2])
    null1.nodeX = 1000
    null1.viewer = True
    out1 = audioreactive_scale.create(td.outCHOP, "out1")
    out1.setInputs([null1])
    out1.nodeX = 1200
    out1.viewer = True

    audioreactive_scale.setInputs([audio_file])


def create_text_layouts():
    """
    Reads a groupings file and creates a Base COMP with Text and Layout TOPs
    for each line. 
    """

    # Open the word groupings file and process each line
    with open(groupings_filename, 'r', encoding='utf-8') as f:
        grouping_data = json.load(f)

    # set background
    background = background_one(parent)

    for i, item in enumerate(grouping_data):
        line = item['group'].strip()  # Remove any leading/trailing whitespace
        if not line:
            continue

        # Calculate the row and column for the current node.
        row = i // NODES_PER_ROW
        col = i % NODES_PER_ROW

        # Create a Base COMP for the group
        base = parent.create(td.baseCOMP, f"group{i}")
        base.viewer = True
        base.nodeX = col * BASE_SPACING
        base.nodeY = row * -BASE_SPACING  # Use negative spacing to build downwards

        # Process the line to fit words within max_chars_per_line
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

        # Create and configure the Layout TOP inside the Base COMP
        make_layout(item['animation_style'], parent, base,
                    processed_lines, item['options'])

        # Set the background
        base.inputConnectors[0].connect(background.outputConnectors[0])

        # Set audioreactive input
        if ("audioreactive_scale" in item['options']):
            base.inputConnectors[1].connect(
                op('audioreactive_scale').outputConnectors[0])


def setup_animation():
    """
    Finds all 'group*' COMPs and connects them to a main Switch TOP using
    connectors. It then creates an Animation COMP to drive the switch.
    """
    # 1. Find all 'group' Base COMPs that were created in the parent.
    all_groups = parent.findChildren(type=td.baseCOMP, name="group*")

    if not all_groups:
        print("No 'group' components found to connect.")
        return

    # Correctly position the switch to the right of the vertical stack of groups
    node_x_start = (NODES_PER_ROW * BASE_SPACING) + 100

    # 2. Create the main Switch TOP
    main_switch = parent.create(td.switchTOP, "mainSwitch")
    main_switch.viewer = True
    main_switch.nodeX = node_x_start

    # --- NEW CONNECTION LOGIC ---
    # Loop through each Base COMP and explicitly connect its first output
    # to the corresponding input on the Switch TOP.
    for i, group_comp in enumerate(all_groups):
        main_switch.inputConnectors[i].connect(group_comp.outputConnectors[0])

    # 3. Set up the Animation COMP to drive the switch
    anim = parent.create(td.animationCOMP, "mainAnimation")
    node_x_start += BASE_SPACING
    anim.nodeX = node_x_start

    # Configure the 'index' channel in the Animation COMP's CHOP data
    channels_dat = anim.op('channels')
    channels_dat.clear(keepFirstRow=True)
    channels_dat.appendRow(
        ['index', 1, 'hold', 'hold', 0, 'keys', 0.3, 0.14, 0.7, 0, 0, 0])

    # 4. Create a Null CHOP to hold the index channel value
    index_out = parent.create(td.nullCHOP, "main_index_out")
    index_out.viewer = True
    node_x_start += BASE_SPACING
    index_out.nodeX = node_x_start
    index_out.inputConnectors[0].connect(anim.outputConnectors[0])

    # Connect the animation to the Switch TOP's index parameter
    main_switch.par.index.expr = f"op('{index_out.name}')['index']"


def create_group_animations():
    matched_timings = find_grouping_times_json(
        groupings_filename, transcript_filename)

    anim = op('mainAnimation')
    keys_dat = anim.op('keys')
    keys_dat.clear(keepFirstRow=True)

    # Append first row at Frame 1
    keys_dat.appendRow([1, 1, 0, 0, 0, "constant()", 0, 0])

    # Loop through groupings and add rows to keys DAT
    for i, item in enumerate(matched_timings):
        start_frame = item["start_time"] * FPS
        keys_dat.appendRow([1, start_frame, i, 0, 0, "constant()", 0, 0])

    # Append last row at last_frame
    keys_dat.appendRow([1, LAST_FRAME, 0, 0, 0, "constant()", 0, 0])

# -----------------
# LAYOUTS
# -----------------


def make_layout(type, parent, base, processed_lines, options):
    # Internal position for operators inside Base COMP
    internal_node_x = 0
    internal_node_y = 0

    # Create in TOP for background
    in_top = base.create(td.inTOP, "in1")
    in_top.viewer = True
    in_top.nodeY = internal_node_y
    internal_node_y -= TOP_SPACING
    internal_node_x += TOP_SPACING
    in_top.nodeX = internal_node_x

    # Create in CHOP for audioreactive scale (if applicable)
    if ("audioreactive_scale" in options):
        in_chop = base.create(td.inCHOP, "in2")
        in_chop.viewer = True
        in_top.nodeY = internal_node_y
        internal_node_y -= TOP_SPACING

    layout = None
    if (type == 'group_basic'):
        layout, internal_node_x, internal_node_y = group_basic_layout(
            parent, base, processed_lines, internal_node_x, internal_node_y)
    elif (type == 'group_rectangular'):
        layout, internal_node_x, internal_node_y = group_rectangular_fit_layout(
            parent, base, processed_lines, internal_node_x, internal_node_y)
    elif (type == 'group_swirl'):
        layout, internal_node_x, internal_node_y = group_swirl(
            parent, base, processed_lines, internal_node_x, internal_node_y)
    elif (type == 'word_basic'):
        layout, internal_node_x, internal_node_y = word_basic(
            parent, base, processed_lines, internal_node_x, internal_node_y)
    elif (type == 'word_impact'):
        layout, internal_node_x, internal_node_y = word_impact(
            parent, base, processed_lines, internal_node_x, internal_node_y)
    else:
        pass

    # Create a composite and level TOP
    comp_top = base.create(td.compositeTOP, "comp1")
    comp_top.setInputs([in_top, layout])
    comp_top.par.operand = 0
    internal_node_x += TOP_SPACING
    comp_top.nodeX = internal_node_x

    level_top = base.create(td.levelTOP, "level1")
    if ("invert_colors" in options):
        level_top.par.invert = 1
    level_top.setInputs([comp_top])
    internal_node_x += TOP_SPACING
    level_top.nodeX = internal_node_x

    # Create an Out TOP and connect Level TOP as Input
    out = base.create(td.outTOP, "out1")
    out.viewer = True
    out.setInputs([level_top])
    internal_node_x += TOP_SPACING
    out.nodeX = internal_node_x

    return


def group_basic_layout(parent, base, processed_lines, internal_node_x, internal_node_y):
    # Create a Text TOP for each processed line
    num_strings_in_list = len(processed_lines)
    all_text_tops = []
    for j, text_line in enumerate(processed_lines):
        text_top = base.create(td.textTOP, f"text{j}")
        text_top.viewer = True
        text_top.par.text = text_line
        text_top.par.font = FONT_NAME
        text_top.par.typeface = FONT_TYPEFACE
        text_top.par.fontsizex = FONT_SIZE
        text_top.par.resolutionw = parent.par.w
        text_top.par.resolutionh = parent.par.h / num_strings_in_list
        text_top.nodeX = internal_node_x
        text_top.nodeY = internal_node_y
        internal_node_y -= TOP_SPACING
        all_text_tops.append(text_top)

    layout = base.create(td.layoutTOP, "layout")
    layout.viewer = True
    layout.par.resolutionw = parent.par.w
    layout.par.resolutionh = parent.par.h
    layout.par.scaleres = 1  # Scale Resolution to Fit
    layout.par.align = 3     # Align: Top to Bottom
    layout.par.fit = 3       # Fit: Fit Best
    internal_node_x += TOP_SPACING
    layout.nodeX = internal_node_x

    # Connect all Text TOPs to the Layout TOP
    layout.setInputs(all_text_tops)

    return layout, internal_node_x, internal_node_y


def group_rectangular_fit_layout(parent, base, processed_lines, internal_node_x, internal_node_y):
    # Create a Text TOP for each processed line
    num_strings_in_list = len(processed_lines)
    all_text_tops = []
    for j, text_line in enumerate(processed_lines):
        text_top = base.create(td.textTOP, f"text{j}")
        text_top.viewer = True
        text_top.par.text = text_line
        text_top.par.font = FONT_NAME
        text_top.par.typeface = FONT_TYPEFACE
        text_top.par.fontsizex = FONT_SIZE
        text_top.par.resolutionw = parent.par.w
        text_top.par.resolutionh = parent.par.h / num_strings_in_list
        text_top.nodeX = internal_node_x
        text_top.nodeY = internal_node_y
        internal_node_y -= TOP_SPACING
        all_text_tops.append(text_top)

    layout = base.create(td.layoutTOP, "layout")
    layout.viewer = True
    layout.par.resolutionw = parent.par.w
    layout.par.resolutionh = parent.par.h
    layout.par.scaleres = 1  # Scale Resolution to Fit
    layout.par.align = 3     # Align: Top to Bottom
    layout.par.fit = 3       # Fit: Fit Best
    internal_node_x += TOP_SPACING
    layout.nodeX = internal_node_x

    # Connect all Text TOPs to the Layout TOP
    layout.setInputs(all_text_tops)

    return layout, internal_node_x, internal_node_y


def group_swirl(parent, base, processed_lines, internal_node_x, internal_node_y):
    # Create a Text TOP for each processed line
    num_strings_in_list = len(processed_lines)
    all_text_tops = []
    for j, text_line in enumerate(processed_lines):
        text_top = base.create(td.textTOP, f"text{j}")
        text_top.viewer = True
        text_top.par.text = text_line
        text_top.par.font = FONT_NAME
        text_top.par.typeface = FONT_TYPEFACE
        text_top.par.fontsizex = FONT_SIZE
        text_top.par.resolutionw = parent.par.w
        text_top.par.resolutionh = parent.par.h / num_strings_in_list
        text_top.nodeX = internal_node_x
        text_top.nodeY = internal_node_y
        internal_node_y -= TOP_SPACING
        all_text_tops.append(text_top)

    layout = base.create(td.layoutTOP, "layout")
    layout.viewer = True
    layout.par.resolutionw = parent.par.w
    layout.par.resolutionh = parent.par.h
    layout.par.scaleres = 1  # Scale Resolution to Fit
    layout.par.align = 3     # Align: Top to Bottom
    layout.par.fit = 3       # Fit: Fit Best
    internal_node_x += TOP_SPACING
    layout.nodeX = internal_node_x

    # Connect all Text TOPs to the Layout TOP
    layout.setInputs(all_text_tops)

    return layout, internal_node_x, internal_node_y


def word_basic(parent, base, processed_lines, internal_node_x, internal_node_y):
    # Create a Text TOP for each word in the line
    all_text_tops = []
    for j, text_line in enumerate(processed_lines):
        text_top = base.create(td.textTOP, f"text{j}")
        text_top.viewer = True
        text_top.par.text = text_line
        text_top.par.font = FONT_NAME
        text_top.par.typeface = FONT_TYPEFACE
        text_top.par.fontsizex = FONT_SIZE
        text_top.par.resolutionw = parent.par.w
        text_top.par.resolutionh = parent.par.h
        text_top.nodeX = internal_node_x
        text_top.nodeY = internal_node_y
        internal_node_y -= TOP_SPACING
        all_text_tops.append(text_top)

    # Create a switch between all text inputs
    switch = base.create(td.switchTOP, "switch")
    switch.viewer = True
    switch.par.resolutionw = parent.par.w
    switch.par.resolutionh = parent.par.h
    internal_node_x += TOP_SPACING
    switch.nodeX = internal_node_x
    switch.nodeY = internal_node_y

    # Connect all Text TOPs to the Switch TOP
    switch.setInputs(all_text_tops)

    # Create animation COMP and add timing
    animation = base.create(td.animationCOMP, "switch_anim")
    internal_node_x += TOP_SPACING
    switch.nodeX = internal_node_x
    switch.nodeY = internal_node_y
    # Configure the 'index' channel in the Animation COMP's CHOP data
    channels_dat = animation.op('channels')
    channels_dat.clear(keepFirstRow=True)
    channels_dat.appendRow(
        ['index', 1, 'hold', 'hold', 0, 'keys', 0.3, 0.14, 0.7, 0, 0, 0])
    # Configure the keys table in the Animation COMP
    keys_dat = animation.op('keys')
    keys_dat.clear(keepFirstRow=True)
    keys_dat.appendRow([1, 1, 0, 0, 0, "constant()", 0, 0]
                       )  # Append first row at Frame 1
    # Find words in transcript and add timings
    # for i, item in enumerate(matched_timings):
    # start_frame = item["start_time"] * FPS
    # keys_dat.appendRow([1, start_frame, i, 0, 0, "constant()", 0, 0])
    # Append last row at last_frame
    keys_dat.appendRow([1, LAST_FRAME, 0, 0, 0, "constant()", 0, 0])

    # create null for index
    index_out = base.create(td.nullCHOP, "index_out")
    internal_node_x += TOP_SPACING
    index_out.nodeX = internal_node_x
    index_out.nodeY -= internal_node_y
    index_out.inputConnectors[0].connect(animation.outputConnectors[0])

    # Connect the animation to the Switch TOP's index parameter
    switch.par.index.expr = f"op('{index_out.name}')['index']"

    return switch, internal_node_x, internal_node_y


def word_impact(parent, base, processed_lines, internal_node_x, internal_node_y):
    # Create a Text TOP for each processed line
    num_strings_in_list = len(processed_lines)
    all_text_tops = []
    for j, text_line in enumerate(processed_lines):
        text_top = base.create(td.textTOP, f"text{j}")
        text_top.viewer = True
        text_top.par.text = text_line
        text_top.par.font = FONT_NAME
        text_top.par.typeface = FONT_TYPEFACE
        text_top.par.fontsizex = FONT_SIZE
        text_top.par.resolutionw = parent.par.w
        text_top.par.resolutionh = parent.par.h / num_strings_in_list
        text_top.nodeX = internal_node_x
        text_top.nodeY = internal_node_y
        internal_node_y -= TOP_SPACING
        all_text_tops.append(text_top)

    layout = base.create(td.layoutTOP, "layout")
    layout.viewer = True
    layout.par.resolutionw = parent.par.w
    layout.par.resolutionh = parent.par.h
    layout.par.scaleres = 1  # Scale Resolution to Fit
    layout.par.align = 3     # Align: Top to Bottom
    layout.par.fit = 3       # Fit: Fit Best
    internal_node_x += TOP_SPACING
    layout.nodeX = internal_node_x

    # Connect all Text TOPs to the Layout TOP
    layout.setInputs(all_text_tops)

    return layout, internal_node_x, internal_node_y

# -----------------
# BACKGROUNDS
# -----------------


def background_one(parent):
    noise = parent.create(td.noiseTOP, 'bg1')
    noise.viewer = True
    noise.par.period = 1.74
    noise.par.harmon = 5
    noise.par.spread = 0.8
    noise.par.gain = 1.34
    noise.par.exp = 2.72
    noise.par.mono = 0
    noise.par.tz.expr = "me.time.frame/100"
    noise.par.resolutionw = parent.par.w
    noise.par.resolutionh = parent.par.h
    noise.nodeX = -BASE_SPACING
    return noise


# -----------------
# EXECUTION
# -----------------
# Clear previous components if they exist to allow for rerunning the script
print("Clearing old components...")
excluded_ops = ['script1', 'script2']
old_components = parent.findChildren(maxDepth=1)
for op_object in old_components:
    if op_object.name in excluded_ops:
        pass
    else:
        op_object.destroy()

# Run the main functions
print("Importing & analyzing audio...")
import_audio()

print("Creating text layouts...")
create_text_layouts()

print("Setting up main animation switch...")
setup_animation()

print("Loading transcript into animation...")
create_group_animations()

print("Script finished.")
