import argparse 
import requests
import bs4
import pandas as pd
import  tqdm 
from urllib.parse import urljoin
import os
from multiprocessing import Pool
import html
from collections import ChainMap


def escape(s):
    try:
        return html.escape(s)
    except:
        return ''

path = './data/'
make_name = lambda x: path + x.replace(" ", '+').replace("/", '-') + ".pdf"


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
                return {open_url: urljoin(open_url, a['href'])}
        return {}
        
    else:
        return {}

def download_pdf(item):
    """
    Downloads the PDF and saves it to `filename`
    """
    title, url = item
    filename = make_name(title)
    if os.path.exists(filename):
        print(f"[!] Already Downloaded {title}... skiping")
        return {url:f'<a href="{filename}">{title}</a>'}


    r = requests.get(url)
    if r.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(r.content)
        return {url:f'<a href="{filename}">{title}</a>'}
    return {}


HTML_PREFIX = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* {
  box-sizing: border-box;
}

#myInput {
  background-position: 10px 10px;
  background-repeat: no-repeat;
  width: 100%;
  font-size: 16px;
  padding: 12px 20px 12px 40px;
  border: 1px solid #ddd;
  margin-bottom: 12px;
}

#myTable {
  border-collapse: collapse;
  width: 100%;
  border: 1px solid #ddd;
  font-size: 18px;
}

#myTable th, #myTable td {
  text-align: left;
  padding: 12px;
}

#myTable tr {
  border-bottom: 1px solid #ddd;
}

#myTable tr.header, #myTable tr:hover {
  background-color: #f1f1f1;
}
</style>
</head>
<body>

<h2>The Textbooks</h2>

<input type="text" id="myInput" onkeyup="myFunction()" placeholder="Search for names.." title="Type in a name">
"""


HTML_SUFFIX = """
<script>
function myFunction() {
  var input, filter, table, tr, td, i, txtValue;
  input = document.getElementById("myInput");
  filter = input.value.toUpperCase();
  table = document.getElementById("myTable");
  tr = table.getElementsByTagName("tr");
  for (i = 0; i < tr.length; i++) {
    td = tr[i].getElementsByTagName("td")[0];
    if (td) {
      txtValue = td.textContent || td.innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }       
  }
}
</script>

</body>
</html>"""




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
        df = pd.read_csv('springer_with_direct_links.csv', index_col=0)

    else:
        df = pd.read_excel(args.springer_filename)
        links = df.OpenURL.values
        

        print("[+] Loaded the Springer files")
        pool = Pool(processes=threads)

        raw_link_map_list = [i for i in tqdm.tqdm(pool.imap_unordered(get_pdf_link, links), total=len(links))]
        raw_link_map = dict(ChainMap(*raw_link_map_list))
        get_link = lambda x: raw_link_map[x]

        df['pdf_links'] = df.OpenURL.apply(get_link)
        df.to_csv("springer_with_direct_links.csv")
    # now we download all the pdfs and write to a file 
    if not os.path.exists(path):
        os.makedirs(path)

    pdf_pool = Pool(processes=threads)
    args = tuple(zip(df["Book Title"].values, df["pdf_links"].values))
    hrefs_map_list = [i for i in tqdm.tqdm(pdf_pool.imap_unordered(download_pdf, args), total=len(args))]

    hrefs_map = dict(ChainMap(*hrefs_map_list))
    get_file = lambda x: hrefs_map[x]
    cols = list(df.columns)
    for column in cols:
        df[column] = df[column].apply(escape)
    df['files'] = df.pdf_links.apply(get_file)

    pd.set_option('display.max_colwidth', -1)
    with open('index_local.html', 'w+') as f:
        html_data =df.sort_values('Subject Classification')[['files'] + cols].to_html(escape=False, table_id='myTable')
        f.write(HTML_PREFIX + html_data + HTML_SUFFIX)







        