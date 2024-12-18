import json
import os
from tqdm import tqdm
import zipfile
import threading
from concurrent.futures import ThreadPoolExecutor

base_path = "loj/"
all_json_files = [f for f in os.listdir(base_path) if f.endswith('_en.json')]
all_json_files = sorted(all_json_files)
print(len(all_json_files))

output_path = base_path + "loj_dataset/"
if not os.path.exists(output_path):
    os.makedirs(output_path)

skip = 0
skip_file_name_list = []
skip_lock = threading.Lock()
cnt = 0
def process_file(name):
    global cnt, skip_file_name_list
    try:
        with open(base_path + name, 'r') as f:
            data = json.load(f)

        # problem.yaml
        try:
            title = data['title']
        except:
            with skip_lock:
                skip_file_name_list.append(name)
            return
        remove_str = title.split(" ")[0] + " "
        title = title.replace(remove_str, "").replace("'", "").replace("\"", "").replace(":", "")
        labels = data['labels']
        tag_list = []
        start = False
        for i in labels:
            if i == "Hide Tags":
                start = True
                continue
            if start:
                tag_list.append(i)
        pid = "L" + data["ID"]
        out_dir = output_path + pid + "/"
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        with open(out_dir + "problem.yaml", 'w') as f:
            f.write(f"title: {title}\n")
            f.write("tag:\n")
            for i in tag_list:
                f.write(f"- {i}\n")
            f.write(f"pid: {pid}\n")

        # problem.md
        content = data['content']
        translated_content = {}
        for key in content.keys():
            if content[key] == "":
                continue
            if key == "题目描述":
                translated_content["Problem Description"] = content[key]
            elif key == "输入格式":
                translated_content["Input Format"] = content[key]
            elif key == "输出格式":
                translated_content["Output Format"] = content[key]
            elif key == "数据范围与提示":
                translated_content["Data Range and Hint"] = content[key]
            elif key.startswith("样例"):
                continue
            else:
                translated_content[key] = content[key]
        content_str = ""
        # generate markdown content
        for key in translated_content.keys():
            content_str += f"## {key}\n\n"
            content_str += translated_content[key] + "\n\n"
        content_str += "## Sample Input\n\n"
        for i, sample in enumerate(data['samples']):
            content_str += f"### Sample Input {i+1}\n\n"
            content_str += "```\n"
            content_str += sample['input'] + "\n"
            content_str += "```\n\n"
            content_str += f"### Sample Output {i+1}\n\n"
            content_str += "```\n"
            content_str += sample['output'] + "\n"
            content_str += "```\n\n"
        with open(out_dir + "problem.md", 'w') as f:
            f.write(content_str)

        # unzip testdata
        testfile = "loj/testdata/TestData_" + name.split("_")[0] + ".zip"
        extract_dir = out_dir + "testdata/"
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)
        try:
            with zipfile.ZipFile(testfile, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except:
            return

        # config.yaml
        time_limit = str(int(data['labels'][1].split(" ")[0])/1000) + "s"
        memory_limit = str(int(data['labels'][2].split(" ")[0]))
        if data['labels'][2].split(" ")[1] == "MiB":
            memory_limit += "mb"
        elif data['labels'][2].split(" ")[1] == "KiB":
            memory_limit += "kb"
        elif data['labels'][2].split(" ")[1] == "GiB":
            memory_limit += "gb"
        with open(extract_dir + "config.yaml", 'w') as f:
            f.write(f"time: {time_limit}\n")
            f.write(f"memory: {memory_limit}\n")
        with threading.Lock():
            cnt += 1
    except Exception as e:
        with skip_lock:
            skip_file_name_list.append(name)

with ThreadPoolExecutor(max_workers=12) as executor:
    list(tqdm(executor.map(process_file, all_json_files), total=len(all_json_files)))

print(f"Total: {cnt}, Skip: {len(skip_file_name_list)}")
with open("skip_file_list.json", 'w') as f:
    json.dump(skip_file_name_list, f)