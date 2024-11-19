
def parse_bruker_log(log_filepath, delim='='):
    """
    Parses a Bruker SkyScan log file to scan metadata.
    TODO: Replace with working code from labdataranger; this works for now
    """
    log_metadata = {}
    with open(log_filepath, 'r') as file:
        for line in file:
            # Example parsing logic: Assume key-value pairs separated by ":"
            if ":" in line:
                key, value = line.strip().split(delim, 1)
                log_metadata[key.strip()] = value.strip()
    return log_metadata
