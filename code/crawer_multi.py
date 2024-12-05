import threading
import os
import queue
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import json
import csv

def create_driver():
	options = Options()
	options.add_argument('--headless')
	options.add_argument('--disable-gpu')
	options.add_argument('--no-sandbox') 
	user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
	options.add_argument(f"user-agent={user_agent}")
	download_dir = "./loj/testdata"
	prefs = {
		"download.default_directory": download_dir,
		"download.prompt_for_download": False,
		"download.directory_upgrade": True,
		"safebrowsing.enabled": True
	}
	options.add_experimental_option("prefs", prefs)

	chromedriver_path = "/home/jianzhu/LLm-pddl-benchmark/code/chromedriver-linux64/chromedriver"
	service = Service(chromedriver_path)
	driver = webdriver.Chrome(service=service, options=options)

	driver.set_page_load_timeout(12000) 
	return driver


def crawl_problem(task_queue, download_dir):
	driver = create_driver()
	while not task_queue.empty():
		try:
			problem = task_queue.get()
			url = problem["Link"]
			problem_id = problem["ID"]
			id = problem["ID"]
			print(f"Thread {threading.current_thread().name} crawling {problem_id}: {url}")
			# if id in skips:
			# 	continue
			if int(id) < 1000:
				continue
			id = id + "."
			loj_file_list = os.listdir("loj")
			has = False
			for loj_file in loj_file_list:
				if id in loj_file:
					has = True
					break
			if has:
				test_file_name = f"TestData_#{problem['ID']}.zip"
				if test_file_name in os.listdir(download_dir):
					continue
			

			try:
				driver.get(url)
				time.sleep(2)
				try:
					title_element = driver.find_element(By.CSS_SELECTOR, "h1.ui.header._header_1rcs8_97 > span")
				except Exception:
					continue
				title = title_element.text.strip()

				labels_section = driver.find_element(By.CSS_SELECTOR, "div._labels_1rcs8_107")

				try:
					show_tags_button = labels_section.find_element(By.CSS_SELECTOR, "a._toggleTagsLabel_1rcs8_113")
					show_tags_button.click()
					time.sleep(1)
				except Exception:
					pass

				labels = []
				labels_elements = labels_section.find_elements(By.CSS_SELECTOR, "div.ui.label, a.ui.label")
				for label in labels_elements:
					labels.append(label.text.strip())

				samples = []
				sample_elements = driver.find_elements(By.CLASS_NAME, "_sampleDataPre_1rcs8_198")
				current_key = "input"
				temp_dict = {}
				for sample_element in sample_elements:
					text = sample_element.text
					temp_dict[current_key] = text
					if current_key == "output":
						samples.append(temp_dict)
						temp_dict = {}
					current_key = "output" if current_key == "input" else "input"
				
				content_sections = driver.find_elements(By.CSS_SELECTOR, "div._markdownContent_1lggv_1")
				content = {}
				headers = driver.find_elements(By.CSS_SELECTOR, "div.ui.large.header")
				for i, section in enumerate(content_sections):
					header_text = headers[i].text.strip() if i < len(headers) else f"Section {i+1}"
					content[header_text] = section.text.strip()

				problem_data = {
					"ID": problem["ID"],
					"title": title,
					"labels": labels,
					"samples": samples,
					"content": content,
					"submissions": problem["Submissions"],
					"acceptance": problem["Acceptance"],
				}

				driver.get(f"{url}/files")
				time.sleep(2)

				# Download test cases
				check_all_checkbox = driver.find_element(By.XPATH, "/html/body/div[1]/div[4]/div/div[1]/div/table/thead/tr/th[1]/div")
				if not check_all_checkbox.is_selected():
					check_all_checkbox.click()
					time.sleep(1)
				time.sleep(1)
				download_button = driver.find_element(By.XPATH, "/html/body/div[1]/div[4]/div/div[1]/div/table/tfoot/tr/th/div/div/div")
				download_button.click()
				time.sleep(1)
				download_button = driver.find_element(By.CSS_SELECTOR, "div.menu.transition.visible._fileTableSelectedFilesDropdownMenu_r2613_51 div.item")
				driver.execute_script("arguments[0].click();", download_button)

				file_name = f"TestData_#{problem["ID"]}.zip"
				start = time.time()
				while True:
					end = time.time()
					if end - start > 300:
						break
					if file_name in os.listdir(download_dir):
						break
					time.sleep(1)
				

				output_file = f"loj/{title.replace(' ', '_').replace("/","_")}.json"
				with open(output_file, "w", encoding="utf-8") as f:
					json.dump(problem_data, f, ensure_ascii=False, indent=4)


				current_directory = os.getcwd()
				total_size = 0

				for filename in os.listdir(current_directory):
					file_path = os.path.join(current_directory, filename)
					
					if os.path.isfile(file_path):
						file_size = os.path.getsize(file_path)
						total_size += file_size

				if total_size / 1024**3 > 500:
					# exit
					break
			except Exception as e:
				print(e)
				continue

			except Exception as e:
				print(f"Error processing problem {problem_id}: {e}")

		except Exception as e:
			print(f"Error in thread {threading.current_thread().name}: {e}")
		finally:
			task_queue.task_done()
	driver.quit()


def main():
	problems = json.load(open("problems.json", "r"))
	task_queue = queue.Queue()
	download_dir = "./loj/testdata"

	for problem in problems:
		task_queue.put(problem)

	thread_count = 56
	threads = []
	for i in range(thread_count):
		t = threading.Thread(target=crawl_problem, args=(task_queue, download_dir), name=f"Thread-{i}")
		threads.append(t)
		t.start()

	for t in threads:
		t.join()

	print("All tasks completed.")

if __name__ == "__main__":
	main()