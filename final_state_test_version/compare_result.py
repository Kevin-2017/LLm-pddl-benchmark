'''
import json
import argparse
import sys

def parse_llm_results(file_path):
    """
    解析 LLM 生成的结果文件并返回状态集合
    :param file_path: LLM 结果文件路径
    :return: 状态集合
    """
    try:
        # 读取文件内容并将每行作为状态
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # 去掉空行并转换为集合
        llm_states = set(line.strip() for line in lines if line.strip())
        return llm_states
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到，请检查文件路径是否正确！")
        return set()
    except Exception as e:
        print(f"读取文件 {file_path} 时发生错误: {e}")
        return set()

def parse_json_results(file_path):
    """
    解析 JSON 文件并返回状态集合
    :param file_path: JSON 文件路径
    :return: 状态集合
    """
    try:
        # 读取JSON文件内容
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # 提取 states_after_actions 的内容并转换为集合
        states_after_actions = data.get("states_after_actions", [])
        if isinstance(states_after_actions, list):
            # 如果是列表，直接将所有状态合并为集合
            json_states = set(states_after_actions)
        elif isinstance(states_after_actions, dict):
            # 如果是字典，合并所有值为集合
            json_states = set()
            for states in states_after_actions.values():
                json_states.update(states)
        else:
            print(f"错误: 'states_after_actions' 格式不支持！")
            return set()

        return json_states
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到，请检查文件路径是否正确！")
        return set()
    except json.JSONDecodeError:
        print(f"文件 {file_path} 不是有效的 JSON 格式！")
        return set()
    except Exception as e:
        print(f"读取文件 {file_path} 时发生错误: {e}")
        return set()

def compare_llm_with_json(llm_states, json_states):
    """
    比较 LLM 的状态与 JSON 的状态
    :param llm_states: LLM 状态集合
    :param json_states: JSON 状态集合
    :return: 是否完全匹配（布尔值）
    """
    return llm_states == json_states

def main():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description="比较 LLM 生成的结果与 JSON 文件中的状态。")
    parser.add_argument(
        "llm_file",
        type=str,
        help="LLM 结果文件的路径（例如：llm_results.txt）"
    )
    parser.add_argument(
        "json_file",
        type=str,
        help="JSON 文件的路径（例如：json_elevator-strips-simple-typed.json）"
    )

    args = parser.parse_args()

    # 解析 LLM 结果
    llm_states = parse_llm_results(args.llm_file)
    if not llm_states:
        print("LLM 结果解析失败，终止程序。")
        sys.exit(1)

    # 解析 JSON 文件
    json_states = parse_json_results(args.json_file)
    if not json_states:
        print("JSON 文件解析失败，终止程序。")
        sys.exit(1)

    # 比较 LLM 与 JSON 内容
    is_match = compare_llm_with_json(llm_states, json_states)

    # 输出比较结果
    if is_match:
        print("TRUE")
    else:
        print("FALSE")

if __name__ == "__main__":
    main()
'''

'''
import json
import argparse
import sys
import re


def parse_llm_results(file_path):
    """
    解析 LLM 生成的结果文件并返回状态集合
    :param file_path: LLM 结果文件路径
    :return: 状态集合
    """
    try:
        # 读取文件内容并将符合括号格式的行作为状态
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # 仅保留带括号的有效状态
        llm_states = set(line.strip() for line in lines if re.search(r"\(.*\)", line))
        return llm_states
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到，请检查文件路径是否正确！")
        return set()
    except Exception as e:
        print(f"读取文件 {file_path} 时发生错误: {e}")
        return set()


def parse_json_results(file_path):
    """
    解析 JSON 文件并返回状态集合
    :param file_path: JSON 文件路径
    :return: 状态集合
    """
    try:
        # 读取JSON文件内容
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # 提取 states_after_actions 的内容并转换为集合
        states_after_actions = data.get("states_after_actions", [])
        if isinstance(states_after_actions, list):
            # 如果是列表，直接将所有符合格式的状态合并为集合
            json_states = set(state for state in states_after_actions if re.search(r"\(.*\)", state))
        elif isinstance(states_after_actions, dict):
            # 如果是字典，合并所有值中符合格式的状态为集合
            json_states = set()
            for states in states_after_actions.values():
                json_states.update(state for state in states if re.search(r"\(.*\)", state))
        else:
            print(f"错误: 'states_after_actions' 格式不支持！")
            return set()

        return json_states
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到，请检查文件路径是否正确！")
        return set()
    except json.JSONDecodeError:
        print(f"文件 {file_path} 不是有效的 JSON 格式！")
        return set()
    except Exception as e:
        print(f"读取文件 {file_path} 时发生错误: {e}")
        return set()


def compare_llm_with_json(llm_states, json_states):
    """
    比较 LLM 的状态与 JSON 的状态
    :param llm_states: LLM 状态集合
    :param json_states: JSON 状态集合
    :return: 是否完全匹配（布尔值）
    """
    return llm_states == json_states


def main():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description="比较 LLM 生成的结果与 JSON 文件中的状态。")
    parser.add_argument(
        "llm_file",
        type=str,
        help="LLM 结果文件的路径（例如：llm_results.txt）"
    )
    parser.add_argument(
        "json_file",
        type=str,
        help="JSON 文件的路径（例如：json_elevator-strips-simple-typed.json）"
    )

    args = parser.parse_args()

    # 解析 LLM 结果
    llm_states = parse_llm_results(args.llm_file)
    if not llm_states:
        print("LLM 结果解析失败，终止程序。")
        sys.exit(1)

    # 解析 JSON 文件
    json_states = parse_json_results(args.json_file)
    if not json_states:
        print("JSON 文件解析失败，终止程序。")
        sys.exit(1)

    # 比较 LLM 与 JSON 内容
    is_match = compare_llm_with_json(llm_states, json_states)

    # 输出比较结果
    if is_match:
        print("TRUE")
    else:
        print("FALSE")


if __name__ == "__main__":
    main()
'''

import json
import argparse
import sys
import re


def parse_llm_results(file_path):
    """
    解析 LLM 生成的结果文件并返回状态集合，仅提取小括号中的内容
    :param file_path: LLM 结果文件路径
    :return: 状态集合
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # 提取每行中小括号内的内容作为有效状态，忽略其他内容
        llm_states = set(re.findall(r"\(.*?\)", line)[0] for line in lines if re.search(r"\(.*?\)", line))
        return llm_states
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到，请检查文件路径是否正确！")
        return set()
    except Exception as e:
        print(f"读取文件 {file_path} 时发生错误: {e}")
        return set()


def parse_json_results(file_path):
    """
    解析 JSON 文件并返回状态集合，仅提取小括号中的内容
    :param file_path: JSON 文件路径
    :return: 状态集合
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # 提取 states_after_actions 的内容并将小括号内的状态加入集合
        states_after_actions = data.get("states_after_actions", [])
        if isinstance(states_after_actions, list):
            # 如果是列表，提取小括号内的内容
            json_states = set(re.findall(r"\(.*?\)", state)[0] for state in states_after_actions if re.search(r"\(.*?\)", state))
        elif isinstance(states_after_actions, dict):
            # 如果是字典，提取每个值中的小括号内容
            json_states = set()
            for state_list in states_after_actions.values():
                json_states.update(re.findall(r"\(.*?\)", state)[0] for state in state_list if re.search(r"\(.*?\)", state))
        else:
            print(f"错误: 'states_after_actions' 格式不支持！")
            return set()

        return json_states
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到，请检查文件路径是否正确！")
        return set()
    except json.JSONDecodeError:
        print(f"文件 {file_path} 不是有效的 JSON 格式！")
        return set()
    except Exception as e:
        print(f"读取文件 {file_path} 时发生错误: {e}")
        return set()


def compare_llm_with_json(llm_states, json_states):
    """
    比较 LLM 的状态与 JSON 的状态
    :param llm_states: LLM 状态集合
    :param json_states: JSON 状态集合
    :return: 是否完全匹配（布尔值）
    """
    return llm_states == json_states


def main():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description="比较 LLM 生成的结果与 JSON 文件中的状态，仅考虑小括号内的内容。")
    parser.add_argument(
        "llm_file",
        type=str,
        help="LLM 结果文件的路径（例如：llm_results.txt）"
    )
    parser.add_argument(
        "json_file",
        type=str,
        help="JSON 文件的路径（例如：json_elevator-strips-simple-typed.json）"
    )

    args = parser.parse_args()

    # 解析 LLM 结果
    llm_states = parse_llm_results(args.llm_file)
    if not llm_states:
        print("LLM 结果解析失败，终止程序。")
        sys.exit(1)

    # 解析 JSON 文件
    json_states = parse_json_results(args.json_file)
    if not json_states:
        print("JSON 文件解析失败，终止程序。")
        sys.exit(1)

    # 比较 LLM 与 JSON 内容
    is_match = compare_llm_with_json(llm_states, json_states)

    # 输出比较结果
    if is_match:
        print("TRUE")
    else:
        print("FALSE")


if __name__ == "__main__":
    main()
