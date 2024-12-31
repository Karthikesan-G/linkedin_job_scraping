
##### Importing required modules #####

import os
import re
import time
import warnings
import requests
import traceback
import random
import pyautogui
import json
import pandas as pd
from selenium import webdriver
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
warnings.filterwarnings("ignore")

today = datetime.now().strftime("%Y-%m-%d")

with open("info.json", 'r', encoding="utf-8") as fh:
    info = json.load(fh) 

info_keywords = info["Match keywords"]
info_user_name = info["User Name"]
info_password = info["Password"]
info_job_location = info["Job Location"]
info_job_title = info["Job Title"]

Cache_path = "Cache/"
if not os.path.exists(Cache_path):
    os.makedirs(Cache_path)

def clean(data):
    data = str(data)
    data = re.sub(r'\s\s+', ' ', data)
    data = re.sub(r'\n', ' ', data)
    data = re.sub(r'\t|\\t', ' ', data)
    data = re.sub(r'<[^>]*?>', ' ', data)
    data = re.sub(r'\s\s+', ' ', data)
    data = re.sub(r'\s*\,\s*$', '', data)
    data = re.sub(r'\s*\.\s*$', '', data)
    data = re.sub(r'\s*$', '', data)
    data = re.sub(r'^\s*', '', data)
    data = re.sub(r'^\s*\|\s*', '', data)
    data = re.sub(r'\s*\|\s*$', '', data)
    data = re.sub(r'\&amp\;', '&', data)
    data = re.sub(r'None', '', data)
    data = re.sub(r'^\s*\:\s*', '', data)
    data = re.sub(r'\s*\:\s*$', '', data)
    data = re.sub(r'\s*\&nbsp;\s*', '', data)
    return data

page_num=1
detail_count=1

output_list = []

header = "SL NO.\tNAME\tDETAIL LINK\tCOMPANY NAME\tSALARY\tLOCATION\tPOSTED TIME\tEASYAPPLY\tWORK MODE\tWORK TYPE\tAPPLIED COUNT\tDESCRIPTION\n"

with open(f"Raw_Output.txt", 'w', encoding='utf-8') as fh:
    fh.write(header)

if __name__ == '__main__':
    
    pid = str(os.getpid())
    print('pid:' + pid)

    options1 = Options()
    options1.add_argument('--disable-blink-features=AutomationControlled')
    options1.add_argument('--start-maximized')
    options1.add_argument("--disable-popup-blocking")
    options1.add_argument('--disable-geolocation') 
    # options1.add_experimental_option('prefs', {
        # "profile.default_content_setting_values.geolocation": 1
    # })
    options1.add_argument("--headless")

    driver = uc.Chrome(options=options1)
    driver.maximize_window()

    driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "accuracy": 100
    })
    action = ActionChains(driver)

    driver.get("https://www.linkedin.com/login")
    time.sleep(2)

    id_element = driver.find_element(By.ID, "username")
    id_element.send_keys(info_user_name)
    time.sleep(2)

    pass_element = driver.find_element(By.ID, "password")
    pass_element.send_keys(info_password)
    time.sleep(2)
    sign_in_button = driver.find_element(By.XPATH, "//button[@aria-label='Sign in']")
    sign_in_button.click()


    driver.get("https://www.linkedin.com/jobs/search/")

    job_role = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[aria-label="Search by title, skill, or company"]'))
    )
    job_role.clear()
    job_role.send_keys(info_job_title)

    job_location = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[aria-label="City, state, or zip code"]'))
    )
    job_location.clear()
    job_location.send_keys(info_job_location)

    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.jobs-search-box__submit-button'))
    )
    search_button.click()
    time.sleep(5)

    # Date Posted Logic - 24 Hours only

    # date_range_button = WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.CSS_SELECTOR, '#searchFilter_timePostedRange'))
    # )
    # date_range_button.click()

    # label_element = driver.find_element(By.CSS_SELECTOR, 'label[for="timePostedRange-r86400"]')

    # action.move_to_element(label_element).click().perform()
    # time.sleep(2)

    # submit_button = WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.XPATH, "//li[div[@data-basic-filter-parameter-name='timePostedRange']]//div[@class='artdeco-hoverable-content__content']//form//fieldset//div[2]//button[2]"))
    # )
    # print(f"{submit_button.text}")
    # submit_button.click()
    # time.sleep(2)

    while True:
        # time.sleep(5)
        list_scroll_block = driver.find_element(By.CSS_SELECTOR, "#main > div > div:nth-of-type(2) > div:first-of-type > div")
        
        #List scroll down logic
        
        total_scroll_height = driver.execute_script("return arguments[0].scrollHeight", list_scroll_block)
        scroll_step = total_scroll_height / 10

        for _ in range(10):
            driver.execute_script("arguments[0].scrollTop += arguments[1]", list_scroll_block, scroll_step)
            time.sleep(2)
        
        time.sleep(5)
        search_Con = driver.page_source

        with open(f"Cache/Sample.html", 'w', encoding='utf-8') as fh:
            fh.write(search_Con)

        ## Detail logic
        
        list_soup = BeautifulSoup(list_scroll_block.get_attribute('outerHTML'), 'html.parser')
        
        job_ids = list_soup.find_all('li', attrs={'id': True})
        # print(clean(str(job_ids)))

        for job_id in job_ids:
            job_id = job_id.get("id")
            print(job_id)
            job_detail_page = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f'//*[@id="{job_id}"]'))
            )
            job_detail_page.click()
            time.sleep(2)
            
            detail_block = driver.find_element(By.CSS_SELECTOR, "#main > div > div:nth-of-type(2) > div:nth-of-type(2)")

            with open(f"Cache/Detail_page_{str(detail_count)}.html", 'w', encoding='utf-8') as fh:
                fh.write(driver.page_source)
            
            try:
                detail_con = driver.execute_script("return arguments[0].outerHTML;", detail_block)
            except Exception as e:
                print(e)
                input()

            detail_soup = BeautifulSoup(detail_con, 'html.parser')

            name=detail_link=location=applied_count=posted_time=company_name=work_mode=salary=work_type=easy_apply=decription= ''
            
            name_obj = detail_soup.h1
            if name_obj:
                name = name_obj.text.strip()
                detail_link_obj = name_obj.find("a")
                if detail_link_obj:
                    detail_link = "https://www.linkedin.com"+detail_link_obj.get('href').split('/?')[0]
            
            job_detail_lists = detail_soup.find(class_="t-black--light mt2")
            if job_detail_lists:
                location_obj = job_detail_lists.find(class_="tvm__text tvm__text--low-emphasis")
                if location_obj:
                    location = location_obj.text.strip()
                posted_time_obj = re.search(r'>\s*([^>]*?\sago)\s*<', str(job_detail_lists), flags=re.I)
                if posted_time_obj:
                    posted_time = posted_time_obj.group(1)
                applied_count_obj = re.search(r'>\s*([^>]*?\s(?:applicants|people\s*clicked\s*apply))\s*<', str(job_detail_lists), flags=re.I)
                if applied_count_obj:
                    applied_count = applied_count_obj.group(1)

            company_name_obj = detail_soup.find(class_="t-14 truncate")
            if company_name_obj:
                company_name_text = company_name_obj.text.strip()
                parts = company_name_text.split(' · ')
                if len(parts) > 0:
                    company_name = parts[0]
                if len(parts) > 1:
                    work_mode_text = parts[1]
                    work_mode_obj = re.search(r'\s*\(\s*([^\)]*?)\)\s*$', str(work_mode_text), flags=re.I)
                    if work_mode_obj:
                        work_mode = work_mode_obj.group(1)
            
            job_details_obj = detail_soup.find(class_="job-details-preferences-and-skills")
            if job_details_obj:
                salary_obj = re.search(r'>\s*([^>]*?(?:\/yr|\₹)[^>]*?)\s*<', str(job_details_obj), flags=re.I)
                if salary_obj:
                    salary = salary_obj.group(1)
                work_type_obj = re.search(r'>\s*(Full\-time|Part\-time|Contract|Temporary|Internship)\s*<', str(job_details_obj), flags=re.I)
                if work_type_obj:
                    work_type = work_type_obj.group(1)
            
            easy_apply_obj = re.search(r">\s*Easy\s*Apply\s*<", str(detail_con), flags=re.I)
            if easy_apply_obj:
                easy_apply = "Yes"
            
            desc_obj = detail_soup.find(class_="jobs-description__container")
            if desc_obj:
                decription = clean(str(desc_obj.text.strip()))
            
            output_dict = {
                "SL NO.": str(detail_count),
                "NAME": str(name), 
                "DETAIL LINK": str(detail_link),
                "COMPANY NAME": str(company_name),
                "SALARY": str(salary),
                "LOCATION": str(location),
                "POSTED TIME": str(posted_time),
                "EASYAPPLY": str(easy_apply),
                "WORK MODE": str(work_mode),
                "WORK TYPE": str(work_type),
                "APPLIED COUNT": str(applied_count),
                "DESCRIPTION": str(decription)
            }

            output_list.append(output_dict)

            data = f"{str(detail_count)}\t{str(name)}\t{str(detail_link)}\t{str(company_name)}\t{str(salary)}\t{str(location)}\t{str(posted_time)}\t{str(easy_apply)}\t{str(work_mode)}\t{str(work_type)}\t{str(applied_count)}\t{str(decription)}\n"

            with open(f"Raw_Output.txt", 'a', encoding='utf-8') as fh:
                fh.write(data)

            detail_count+=1
        
        with open(f"Cache/List_page_{str(page_num)}.html", 'w', encoding='utf-8') as fh:
            fh.write(list_scroll_block.get_attribute('outerHTML'))
        page_num+=1
        
        try:
            next_page = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="View next page"]'))
            )
            next_page.click()
        except Exception as e:
            print("No more pages to click.")
            break

    df = pd.DataFrame(output_list)

    # remove dups
    df = df.drop_duplicates(subset=['NAME','COMPANY NAME','DESCRIPTION'])

    keywords = info_keywords

    keywords_text = " ".join(keywords)

    documents = df['DESCRIPTION'].tolist() + [keywords_text]
    vectorizer = TfidfVectorizer(stop_words='english')

    tfidf_matrix = vectorizer.fit_transform(documents)
    cosine_similarities = cosine_similarity(tfidf_matrix[:-1], tfidf_matrix[-1:]) 

    percentage_matches = cosine_similarities.flatten() * 100


    #sorting percentage
    df['Match_Percentage'] = percentage_matches
    df['Match_Percentage'] = df['Match_Percentage'].astype(int)
    df = df.sort_values(by='Match_Percentage', ascending=False)
    df['Match_Percentage'] = df['Match_Percentage'].apply(lambda x: f"{x:.2f}%")

    df.drop('SL NO.', axis=1, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.index = df.index + 1
    df.index.name = 'SL NO.'

    df.to_excel("LinkedIn_Output.xlsx")

