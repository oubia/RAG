import pandas as pd
from bs4 import BeautifulSoup
import re
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getenv("PYTHONPATH"))

input_file = 'src/data/d7_tper_pages.csv'  
output_file = 'src/data/cleaned_version.csv'  

df = pd.read_csv(input_file, header=None, names=['date', 'page_title', 'content','NaN'])


df.reset_index(inplace=True)
df.rename(columns={'index': 'id'}, inplace=True)


def clean_content(content):
    if pd.isna(content) or not content.strip():
        return None 
    soup = BeautifulSoup(content, 'html.parser')
    
    for a_tag in soup.find_all('a', href=True):
        link = a_tag.get('href', '')
        a_tag.replace_with(link) 
    
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    
    text = soup.get_text(separator=" ")
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

df['content'] = df['content'].apply(clean_content)

df = df.dropna(subset=['content'])
df = df[df['content'].str.strip().astype(bool)]



del df['NaN']

df = df[df['content'].notna()]

df['page_link'] = df['id'].apply(lambda x: f"https://www.tper.it/node/{x}")

df.to_csv(output_file, index=False)
print("Cleaned content saved to:", output_file)
