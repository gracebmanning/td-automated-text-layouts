import json
import string


def clean_word(word):
    """
    Cleans a word by standardizing apostrophes, converting to lowercase,
    and removing other punctuation.
    """
    # Standardize different types of apostrophes and quotes to a single straight quote
    # This handles characters like ‘, ’, and `
    word = word.replace("’", "'").replace("‘", "'").replace("`", "'")

    # Create a translator that removes all punctuation EXCEPT the now-standardized apostrophe
    translator = str.maketrans('', '', string.punctuation.replace("'", ""))
    result = word.lower().translate(translator)
    return result


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


def find_grouping_times_json(groupings_file_path, transcript_file_path):
    """
    Matches word groupings from a JSON file to a transcript JSON file
    to determine the start and end time of each grouping.

    Args:
        groupings_file_path (str): The path to the JSON file containing word groupings (one per line).
        transcript_file_path (str): The path to the JSON file containing word-level timestamps.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              grouping, its start time, and its end time. Returns an empty
              list if files cannot be read or no matches are found.
    """
    try:
        # Read the transcript data from the JSON transcript file
        with open(transcript_file_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)

        # Read the groupings from the JSON groupings file
        with open(groupings_file_path, 'r', encoding='utf-8') as f:
            grouping_data = json.load(f)

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
    for item in grouping_data:
        group = item["group"]
        grouping_words = group.split()
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
                    'grouping': group,
                    'start_time': start_time,
                    'end_time': end_time
                })

                # Move the cursor to the position after the found match
                # This ensures we search for the next grouping from this point onward
                transcript_cursor = end_word_index + 1
                break  # Stop searching for this grouping and move to the next one

    return results


if __name__ == "__main__":
    transcript_filename = "../../input_files/attentionIsAllYouNeed1_transcript.json"
    groupings_filename = "../../input_files/attentionIsAllYouNeed1_groupings.json"
    results = find_grouping_times_json(groupings_filename, transcript_filename)

    output_json_path = "./testing/testing_output_4.json"
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
        print(
            f"\nFull recursive alignment results saved to: {output_json_path}")
