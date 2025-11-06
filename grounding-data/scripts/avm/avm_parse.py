from pathlib import Path
import re

def search_in_file(file_path):
    pattern_topic = r"This (?:.*) (?:deploys|creates|represents|provides) (.+?)\..*\n"
    pattern_example = r"Example \d+: _(.*?)_\n.*```bicep\n(.*?)```"
    with open(file_path, 'r', encoding='utf-8') as file:
        file_contents = file.read()
        match_topic = re.search(pattern_topic, file_contents)
        if match_topic:
            matches_example = re.findall(pattern_example, file_contents, re.DOTALL)
            for match in matches_example:            
                with open('train.jsonl', 'a', encoding='utf-8-sig') as file:
                    file.write('{"messages": [{"role": "system", "content": "Generate an Azure Resource Manager (ARM) template in Bicep format according to the user\'s request."}, {"role": "user", "content": "Deploy {topic}: {subtopic}"}, {"role": "assistant", "content": "{code}"}]}\n'.format(topic=match_topic.group(1), subtopic=match[0], code=' '.join(match[1].replace('\n', '\\n').split())))

def search_files_with_pathlib(base_dir, partial_path):
   base = Path(base_dir)
   for path in base.rglob("*"):
       if partial_path in str(path):
           search_in_file(path)

# Example usage
base_directory = "./"
partial_file_path = "README.md"
search_files_with_pathlib(base_directory, partial_file_path)