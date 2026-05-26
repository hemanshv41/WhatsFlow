import re
import pandas as pd

def clean_txt(line):
    """
    Cleans hidden unicode formatting characters (like LTR/RTL marks)
    commonly found in WhatsApp iOS export files.
    """
    return line.replace('\u200e', '').replace('\u200f', '').strip()

def preprocess(data):
    """
    INTERVIEW TALKING POINTS:
    - This function converts raw WhatsApp text into a clean Pandas DataFrame.
    - It reads the file line-by-line.
    - Multi-line messages are handled by appending text to the previous message.
    - System notifications are separated from user messages.
    """
    if isinstance(data, str):
        lines = data.split('\n')
    else:
        lines = data
        
    messages = []
    current_msg = None
    
    # REGEX PATTERN EXPLANATION FOR INTERVIEW:
    # ^\[?          -> (Optional) bracket for iOS timestamps
    # (             -> Start date-time capture group
    #   \d{1,2}/\d{1,2}/\d{2,4} -> Matches dates like 12/24/20 or 24/12/2026
    #   ,\s         -> Matches comma and space separating date and time
    #   \d{1,2}:\d{2}(?::\d{2})? -> Matches hours:minutes (and optional :seconds)
    #   (?:\s?[APap][Mm])?       -> Matches optional AM/PM markers
    # )             -> End date-time capture group
    # \]?           -> (Optional) bracket for iOS timestamps
    # \s?           -> Optional space
    # (?:-\s)?      -> (Optional) hyphen and space for Android format
    # (.*)$         -> Captures everything else on the line (sender + message)
    pattern = r'^\[?(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap][Mm])?)\]?\s?(?:-\s)?(.*)$'
    
    for line in lines:
        if not line.strip():
            continue
            
        line_clean = clean_txt(line)
        match = re.match(pattern, line_clean)
        
        if match:
            # If we were building a previous message, save it first
            if current_msg:
                messages.append(current_msg)
                
            timestamp = match.group(1)
            content = match.group(2)
            
            # Split sender and message by first occurrence of ": "
            parts = content.split(': ', 1)
            
            if len(parts) == 2:
                # Standard user message: "Sender Name: Message content"
                sender = parts[0].strip()
                message = parts[1].strip()
                is_system = False
            else:
                # System message (no colon): "You created this group" or "Messages are encrypted"
                sender = "System Alert"
                message = content.strip()
                is_system = True
                
            current_msg = {
                'date_str': timestamp,
                'sender': sender,
                'message': message,
                'is_system': is_system
            }
        else:
            # Multi-line message continuation (no timestamp header matched)
            if current_msg:
                current_msg['message'] += ' ' + line_clean
                
    # Add final message
    if current_msg:
        messages.append(current_msg)
        
    df = pd.DataFrame(messages)
    
    if df.empty:
        return pd.DataFrame(columns=['date', 'sender', 'message', 'is_system', 'hour', 'day_name'])
        
    # Convert date string to actual Datetime object (use mixed for flexibility)
    df['date'] = pd.to_datetime(df['date_str'], format='mixed', errors='coerce')
    df = df.dropna(subset=['date']) # Drop any rows where dates failed to parse
    df = df.drop(columns=['date_str'])
    
    # Extract simple attributes for easy chart grouping
    df['hour'] = df['date'].dt.hour
    df['day_name'] = df['date'].dt.day_name()
    
    return df
