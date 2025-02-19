import re
import csv

def extract_pcre_fields(file_path):
    pcre_pattern = re.compile(r'pcre:"([^"]+)"')
    pcre_fields = set()

    with open(file_path, 'r') as file:
        for line in file:
            match = pcre_pattern.search(line)
            if match:
                pcre_fields.add(match.group(1))

    return pcre_fields

# 示例用法
input_path = 'G:\shared\snort3-community-rules\snort3-community-rules\snort3-community.rules'
output_path = './pcre_fields.csv'

pcre_fields = extract_pcre_fields(input_path)

with open(output_path, 'w', newline='') as output_file:
    writer = csv.writer(output_file)
    for pcre in pcre_fields:
        writer.writerow([pcre])
        # 将每个PCRE字段写入一行，以CSV格式保存
        print(pcre)