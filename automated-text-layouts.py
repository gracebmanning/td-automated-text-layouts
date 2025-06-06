# -----------------
# USER PARAMETERS
# -----------------
# File paths for the transcript and word groupings
transcript_filename = "./InputFiles/attentionIsAllYouNeed1_transcript.json"
groupings_filename = "./InputFiles/attentionIsAllYouNeed1_groupings.txt"

# Font styling
font_name = "Gigi"
font_typeface = "Regular"
font_size = 30

# The maximum number of characters allowed on a single line of text.
# The user must determine this value based on the chosen font and font size.
MAX_CHARS_PER_LINE = 30

# node layout spacing
BASE_SPACING = 150
TOP_SPACING = 200

# The parent component where all new operators will be created.
# This script assumes it is running from within the target parent container.
parent = me.parent()


# -----------------
# SCRIPT LOGIC
# -----------------


def create_text_layouts():
    """
    Reads a groupings file and creates a Base COMP with Text and Layout TOPs
    for each line. 
    """
    # X position for the Base COMPs in the parent container
    base_node_y = 0

    # Open the word groupings file and process each line
    with open(groupings_filename, 'r') as f:
        group_lines = f.readlines()

    for i, line in enumerate(group_lines):
        line = line.strip()  # Remove any leading/trailing whitespace
        if not line:
            continue

        # 1. Create a Base COMP for the group
        base = parent.create(baseCOMP, f"group{i}")  # type: ignore
        base.nodeY = base_node_y
        base_node_y += BASE_SPACING  # Increment X position for the next Base COMP

        internal_node_x = 0  # Internal position for operators inside Base COMP

        # 2. Create and configure the Layout TOP inside the Base COMP
        layout = base.create(layoutTOP, "layout")
        layout.par.resolutionw = parent.par.w
        layout.par.resolutionh = parent.par.h
        layout.par.scaleres = 1  # Scale Resolution to Fit
        layout.par.align = 3     # Align: Top to Bottom
        layout.par.fit = 3       # Fit: Fit Best

        layout.nodeX = internal_node_x-TOP_SPACING  # Set position

        # 3. Process the line to fit words within max_chars_per_line
        words = line.split()
        processed_lines = []
        current_line = ""

        for word in words:
            # Check if adding the next word exceeds the max character limit
            if len(current_line) + len(word) + 1 > MAX_CHARS_PER_LINE:
                processed_lines.append(current_line)
                current_line = word
            else:
                if current_line:
                    current_line += f" {word}"
                else:
                    current_line = word
        processed_lines.append(current_line)

        # 4. Create a Text TOP for each processed line
        num_strings_in_list = len(processed_lines)
        for j, text_line in enumerate(processed_lines):
            text_top = base.create(textTOP, f"text{j}")
            text_top.viewer = True

            # Set text content and styling
            text_top.par.text = text_line
            text_top.par.font = font_name
            text_top.par.typeface = font_typeface
            text_top.par.fontsizex = font_size

            # Set resolution based on the number of lines
            text_top.par.resolutionw = parent.par.w
            text_top.par.resolutionh = parent.par.h / num_strings_in_list

            # Set position
            text_top.nodeX = internal_node_x
            internal_node_x += TOP_SPACING  # Increment for the next Text TOP

        # 5. Connect all Text TOPs to the Layout TOP
        all_text_tops = base.findChildren(type=textTOP, name="text*")
        if all_text_tops:
            layout.setInputs(all_text_tops)

        # 6. Create an Out TOP and connect Layout TOP as Input
        out = base.create(outTOP, "out", initialize=True)
        out.setInputs(base.findChildren(name="layout"))
        out.nodeX = internal_node_x


def setup_animation():
    """
    Finds all 'group*' COMPs and connects them to a main Switch TOP. It then
    creates an Animation COMP to drive the switch.
    """
    # 1. Find all 'group' Base COMPs that were created in the parent.
    # The findChildren() method returns them in alphanumeric order by name.
    all_groups = parent.findChildren(type=baseCOMP, name="group*")

    # Determine start position for new nodes based on the last group's position
    node_x_start = 0
    if all_groups:
        # Sort groups by their nodeX to find the last one
        all_groups.sort(key=lambda op: op.nodeX)
        node_x_start = all_groups[-1].nodeX + BASE_SPACING + 25

    if not all_groups:
        print("No 'group' components found to connect.")
        return

    # 2. Create a main Switch TOP and connect all Base COMPs using findChildren()
    main_switch = parent.create(switchTOP, "mainSwitch")
    main_switch.nodeX = node_x_start
    main_switch.setInputs(all_groups)

    # 3. Set up the Animation COMP to drive the switch
    anim = parent.create(animationCOMP, "mainAnimation")
    anim.nodeX = node_x_start + BASE_SPACING

    # Configure the 'index' channel in the Animation COMP's CHOP data
    channels_dat = anim.op('channels')
    channels_dat.clear(keepFirstRow=True)
    channels_dat.appendRow(
        ['index', 1, 'hold', 'hold', 0, 'keys', 0.3, 0.14, 0.7, 0, 0, 0])

    # Connect the animation to the Switch TOP's index parameter
    main_switch.par.index.expr = f"op('{anim.name}')['index']"

    # NOTE: The logic to parse the transcript file and create the actual keyframes
    # in the 'mainAnimation' COMP still needs to be implemented. This script
    # successfully builds and connects the necessary operators.


# -----------------
# EXECUTION
# -----------------
# Clear previous components if they exist to allow for rerunning the script
print("Clearing old components...")
old_components = []
old_components.extend(parent.findChildren(name="group*"))
old_components.extend(parent.findChildren(name="mainSwitch"))
old_components.extend(parent.findChildren(name="mainAnimation"))
for opName in old_components:
    op(opName).destroy()

# Run the main functions
print("Creating text layouts...")
create_text_layouts()

print("Setting up main animation switch...")
setup_animation()

print("Script finished.")
