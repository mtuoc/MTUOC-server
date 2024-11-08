import re

class TagsSegmenter:
    def __init__(self):
        pass

    def segment(self, text):
        # Regular expression to match tags and text
        pattern = re.compile(r'(<[^>]+>|[^<>]+)')
        # Find all matches (either tags or non-tag text)
        segments = pattern.findall(text)
        
        # Return the list of segments
        return segments

    def segmentList(self, texts):
        # Initialize an empty list to hold all segments
        all_segments = []

        # Iterate through the list of strings
        for text in texts:
            # Update the instance text for each string
            
            # Append the segments from this string to the result list
            all_segments.extend(self.segment(text))
        
        # Return the combined list of segments
        return all_segments

