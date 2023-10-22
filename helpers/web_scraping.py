# @packages
from bs4 import BeautifulSoup
import os
import requests
import re


"""
A collection of simple web scraping functions with BeautifulSoup. 
For more advanced use cases see Scrapy or Selenium.
"""


def get_data(url):
  """
  Gets the text data from a website url.
  Accepts the URL for the website. 
  Returns a text file of the HTML. 
  """
  res = requests.get(url)
  
  return res.text


def get_links(website_link):
  """
  Gets hyperlinks to other pages on the website.
  Accepts the URL for the website. 
  Returns a list of links without duplicates. 
  """
  html_data = get_data(website_link)
  soup = BeautifulSoup(html_data, "html.parser")
  
  list_links = []
  for link in soup.find_all("a", href=True):
    list_links.append(link.get("href"))
    
  # Remove duplicates 
  list_links = list(set(list_links))
        
  return list_links


def add_base_path(website_link, list_links):
  """
  Ensures links have a base path.
  Accepts the website URL & a list of parsed links.
  Returns the processed links.
  """
  list_links_with_base_path = []
  
  # Remove the '/' from the website link if present
  if website_link.endswith('/'):
    website_link = website_link[:-1]
  
  # Iterate through the provided list & process as desired
  for link in list_links:
    if link.startswith('/'):
      link_with_base_path = website_link + link
      list_links_with_base_path.append(link_with_base_path)

    elif link.startswith('http://') | link.startswith('https://'):
      list_links_with_base_path.append(link)

    elif link.startswith('./'):
      link_with_base_path = website_link + link.split('.')[-1]
      list_links_with_base_path.append(link_with_base_path)
      
  # Ensure the website URL is in the list
  if website_link not in list_links_with_base_path and (website_link + '/') not in list_links_with_base_path:
    print("Link not found")
    list_links_with_base_path.append(website_link)

  return list_links_with_base_path


def save_content(link_list, folder_name):
  """
  Downloads HTML text content from a list a web links & persists this data to .txt files.
  Accepts a list of web links and the name of the folder to persist output files.
  Saves the files within the folder_name provided in the current working directory.
  """
  for i, link in enumerate(link_list):
    html_data = get_data(link)
    soup = BeautifulSoup(html_data, "html.parser")
    text = soup.get_text()

    # Get the first 3 words in the cleaned text
    words = text.split()[:3]
    file_name_prefix = "_".join(words)

    # Replace special characters and spaces with an underscore
    file_name_prefix = re.sub(r"[^a-zA-Z0-9]+", "_", file_name_prefix)

    # Get the current working directory
    current_dir = os.getcwd()

    # Set the path to the data folder
    data_folder = os.path.join(current_dir, folder_name)

    # Create the data folder if it doesn't exist
    if not os.path.exists(data_folder):
      os.makedirs(data_folder)

    # Set the path to the output file
    output_file = os.path.join(data_folder, f"{i}_{file_name_prefix}.txt")

    # Save the text content to the output file
    with open(output_file, "w") as f:
      f.write(text)


def web_scrape_site(website_url, folder_name):
  """
  Executes the functions above for web scrapping the text from a website.
  Accepts the website URL and the name of a folder to persist the .txt files.
  Currently called on line: 193 of app.py
  """
  sub_links = get_links(website_url)
  link_list = add_base_path(website_url, sub_links)
  save_content(link_list, folder_name)
  