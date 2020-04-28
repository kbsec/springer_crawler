import argparse 
import requests
import bs4
import pandas as pd
import  tqdm 
from urllib.parse import urljoin
import os
from multiprocessing import Pool


path = './data/'
make_name = lambda x: path + x.replace(" ", '+') + ".pdf"


def get_pdf_link(open_url):

    """
    Grabs the PDF link. 
    """
    href_key = "Book download - pdf"

    r = requests.get(open_url)
    if r.status_code == 200:
        soup = bs4.BeautifulSoup(r.text, 'lxml')
        for a in soup.find_all('a', href=True):
            if 'data-track-action' in a.attrs:
                return urljoin(open_url, a['href'])
        return False
        
    else:
        return False

def download_pdf(item):
    """
    Downloads the PDF and saves it to `filename`
    """
    title, url = item
    filename = make_name(title)
    if os.path.exists(filename):
        print(f"[!] Already Downloaded {title}... skiping")
        return f'<a href="{filename}">{title}</a>'


    r = requests.get(url)
    if r.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(r.content)
        return f'<a href="{filename}">{title}</a>'
    return False 



if __name__ == '__main__':
    # Table for preventing duplicate crawls

    parser = argparse.ArgumentParser()
    # CLI parser
    parser.add_argument('--threads', type=int,
                    default=10, help='Number of threads')

    parser.add_argument('--springer_filename', type=str,
                    default="Free+English+textbooks.xlsx", help="Springer Excel file containing free books! \n \
                    See https://www.springernature.com/gp/librarians/news-events/all-news-articles/industry-news-initiatives/free-access-to-textbooks-for-institutions-affected-by-coronaviru/17855960 ")    


    args = parser.parse_args()
    threads = args.threads
    if  os.path.exists('springer_with_direct_links.csv'):
        df = pd.read_csv('springer_with_direct_links.csv')

    else:
        df = pd.read_excel(args.springer_filename)
        links = df.OpenURL.values
        

        print("[+] Loaded the Springer files")
        pool = Pool(processes=threads)

        raw_links = [i for i in tqdm.tqdm(pool.imap_unordered(get_pdf_link, links), total=len(links))]

        df['pdf_links'] = raw_links
        df.to_csv("springer_with_direct_links.csv")
    # now we download all the pdfs and write to a file 
    if not os.path.exists(path):
        os.makedirs(path)

    pdf_pool = Pool(processes=threads)
    args = tuple(zip(df["Book Title"].values, df["pdf_links"].values))
    hrefs = [i for i in tqdm.tqdm(pdf_pool.imap_unordered(download_pdf, args), total=len(args))]
    df['files'] = hrefs
    with open('index.html', 'w+') as f:
        f.write(df.to_html(escape=False))




        