import json
import string


def clean_word(word):
    """
    Cleans a word by standardizing apostrophes, converting to lowercase,
    and removing other punctuation. This ensures consistent matching.
    """
    # Standardize different types of apostrophes (curly vs. straight)
    word = word.replace("’", "'").replace("‘", "'").replace("`", "'")
    # Define punctuation to remove, but keep the standard apostrophe
    translator = str.maketrans('', '', string.punctuation.replace("'", ""))
    return word.lower().translate(translator)


def find_word_level_times(groupings_file_path, transcript_file_path):
    """
    Matches word groupings from a JSON file to a transcript JSON file and
    enriches the grouping data with word-level start and end times for
    each specific match.

    Args:
        groupings_file_path (str): Path to the JSON file with word groupings and animation data.
        transcript_file_path (str): Path to the JSON file with word-level timestamps.

    Returns:
        list: A list of dictionaries, where each dictionary contains the original
              grouping data, the group's overall start/end times, and a new 'words'
              key containing a list of individual word timings.
    """
    try:
        with open(transcript_file_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        with open(groupings_file_path, 'r', encoding='utf-8') as f:
            grouping_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Could not find the file - {e.filename}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {e.doc}. Please check file format.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

    # Clean the words in the transcript data for easier matching
    cleaned_transcript_words = [clean_word(
        item['word']) for item in transcript_data]

    results = []  # The results list will store our new, enriched data
    transcript_cursor = 0  # This pointer keeps track of our position in the transcript

    # Iterate through each item in your groupings.json
    for grouping_item in grouping_data:
        group_text = grouping_item.get("group", "")
        if not group_text:
            continue

        grouping_words = group_text.split()
        cleaned_grouping_words = [clean_word(word) for word in grouping_words]
        num_grouping_words = len(cleaned_grouping_words)

        # Search for the word sequence in the transcript, starting from the cursor
        for i in range(transcript_cursor, len(cleaned_transcript_words) - num_grouping_words + 1):
            transcript_slice = cleaned_transcript_words[i: i +
                                                        num_grouping_words]

            if transcript_slice == cleaned_grouping_words:
                # --- Match Found! ---
                start_word_index = i
                end_word_index = i + num_grouping_words - 1

                # 1. Get overall start/end times for the whole group
                group_start_time = transcript_data[start_word_index]['start']
                group_end_time = transcript_data[end_word_index]['end']

                # 2. Get word-level details for this specific match
                word_level_details = []
                for word_index in range(start_word_index, end_word_index + 1):
                    word_obj = transcript_data[word_index]
                    word_level_details.append({
                        "word": word_obj['word'],
                        "start": word_obj['start'],
                        "end": word_obj['end']
                    })

                # 3. Build the new result object
                # Start with original data (group, style, etc.)
                new_result_item = grouping_item.copy()
                new_result_item['start_time'] = group_start_time
                new_result_item['end_time'] = group_end_time
                # Add the detailed word timings
                new_result_item['words'] = word_level_details

                results.append(new_result_item)

                # 4. Move the cursor past this match to find the next one
                transcript_cursor = end_word_index + 1
                break  # Stop searching for this group and move to the next

    return results


if __name__ == '__main__':
    # Define the paths to your input files
    groupings_json_file = '../../input_files/attentionIsAllYouNeed1_groupings.json'
    transcript_json_file = '../../input_files/attentionIsAllYouNeed1_transcript.json'

    # Generate the detailed timing data
    animation_data = find_word_level_times(
        groupings_json_file, transcript_json_file)

    # Save the enriched data to a new file for use in TouchDesigner
    output_filename = './testing/attentionIsAllYouNeed1_animation_data.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(animation_data, f, indent=4)

    print(
        f"Successfully generated detailed animation data and saved it to '{output_filename}'")
    if not animation_data:
        print("Warning: The output file is empty. Check that the input files exist and are correctly formatted.")
