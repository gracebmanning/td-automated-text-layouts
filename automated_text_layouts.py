import json
import string
# -----------------
# USER PARAMETERS
# -----------------
# File paths for the transcript and word groupings
transcript_filename = "./InputFiles/attentionIsAllYouNeed1_transcript.json"
groupings_filename = "./InputFiles/attentionIsAllYouNeed1_groupings.txt"

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
TOP_SPACING = 200


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

        # Calculate the row and column for the current node.
        row = i // NODES_PER_ROW
        col = i % NODES_PER_ROW

        # 1. Create a Base COMP for the group
        base = parent.create(baseCOMP, f"group{i}")
        base.viewer = True
        base.nodeX = col * BASE_SPACING
        base.nodeY = row * -BASE_SPACING  # Use negative spacing to build downwards

        # Internal position for operators inside Base COMP
        internal_node_x = 0
        internal_node_y = 0

        # 2. Process the line to fit words within max_chars_per_line
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

        # 3. Create a Text TOP for each processed line
        num_strings_in_list = len(processed_lines)
        for j, text_line in enumerate(processed_lines):
            text_top = base.create(textTOP, f"text{j}")
            text_top.viewer = True
            text_top.par.text = text_line
            text_top.par.font = font_name
            text_top.par.typeface = font_typeface
            text_top.par.fontsizex = font_size
            text_top.par.resolutionw = parent.par.w
            text_top.par.resolutionh = parent.par.h / num_strings_in_list
            text_top.nodeX = internal_node_x
            text_top.nodeY = internal_node_y
            internal_node_y -= TOP_SPACING

        # 4. Create and configure the Layout TOP inside the Base COMP
        layout = base.create(layoutTOP, "layout")
        layout.viewer = True
        layout.par.resolutionw = parent.par.w
        layout.par.resolutionh = parent.par.h
        layout.par.scaleres = 1  # Scale Resolution to Fit
        layout.par.align = 3     # Align: Top to Bottom
        layout.par.fit = 3       # Fit: Fit Best
        internal_node_x += TOP_SPACING
        layout.nodeX = internal_node_x

        # 5. Connect all Text TOPs to the Layout TOP
        all_text_tops = base.findChildren(type=textTOP, name="text*")
        if all_text_tops:
            layout.setInputs(all_text_tops)

        # 6. Create an Out TOP and connect Layout TOP as Input
        out = base.create(outTOP, "out1")
        out.viewer = True
        out.setInputs(base.findChildren(name="layout"))
        internal_node_x += TOP_SPACING
        out.nodeX = internal_node_x


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

# NOTE: The logic to parse the transcript file and create the actual keyframes
# in the 'mainAnimation' COMP still needs to be implemented. This script
# successfully builds and connects the necessary operators.


def clean_word(word):
    """
    Cleans a word by converting it to lowercase and removing punctuation.
    """
    # Remove punctuation, but keep apostrophes for contractions like "you'll"
    translator = str.maketrans('', '', string.punctuation.replace("'", ""))
    return word.lower().translate(translator)


def find_grouping_times(groupings_file_path, transcript_file_path):
    """
    Matches word groupings from a text file to a transcript JSON file
    to determine the start and end time of each grouping.

    Args:
        groupings_file_path (str): The path to the text file containing word groupings (one per line).
        transcript_file_path (str): The path to the JSON file containing word-level timestamps.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              grouping, its start time, and its end time. Returns an empty
              list if files cannot be read or no matches are found.
    """
    try:
        # Read the transcript data from the JSON file
        with open(transcript_file_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)

        # Read the groupings from the text file
        with open(groupings_file_path, 'r', encoding='utf-8') as f:
            groupings = [line.strip() for line in f if line.strip()]

    except FileNotFoundError as e:
        print(f"Error: Could not find the file - {e.filename}")
        return []
    except json.JSONDecodeError:
        print(
            f"Error: Could not decode JSON from {transcript_file_path}. Please check its format.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

    # Clean the words in the transcript data for easier matching
    cleaned_transcript_words = [clean_word(
        item['word']) for item in transcript_data]

    results = []
    transcript_cursor = 0  # This pointer keeps track of our position in the transcript

    # Iterate over each grouping to find its match in the transcript
    for grouping in groupings:
        grouping_words = grouping.split()
        if not grouping_words:
            continue

        cleaned_grouping_words = [clean_word(word) for word in grouping_words]
        num_grouping_words = len(cleaned_grouping_words)

        # Search for the sequence of words in the transcript, starting from the cursor
        for i in range(transcript_cursor, len(cleaned_transcript_words) - num_grouping_words + 1):
            # Check if the slice of transcript words matches the current grouping
            transcript_slice = cleaned_transcript_words[i: i +
                                                        num_grouping_words]

            if transcript_slice == cleaned_grouping_words:
                # Match found!
                start_word_index = i
                end_word_index = i + num_grouping_words - 1

                # Get the start time from the first word of the match
                start_time = transcript_data[start_word_index]['start']
                # Get the end time from the last word of the match
                end_time = transcript_data[end_word_index]['end']

                results.append({
                    'grouping': grouping,
                    'start_time': start_time,
                    'end_time': end_time
                })

                # Move the cursor to the position after the found match
                # This ensures we search for the next grouping from this point onward
                transcript_cursor = end_word_index + 1
                break  # Stop searching for this grouping and move to the next one

    return results


def parse_transcript():
    matched_timings = find_grouping_times(
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
parse_transcript()

print("Script finished.")
