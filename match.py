import re

def find_regex_matches(long_string, pattern):
    matches = re.finditer(pattern, long_string)
    for match in matches:
        start, end = match.span()
        print(f"Match found from {start} to {end}: {match.group()}")

# 示例用法
if __name__ == "__main__":
    long_string = "This is a test string with some test patterns like test123 and test456."
    pattern = r"test\d*"
    find_regex_matches(long_string, pattern)