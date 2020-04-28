# springer_crawler
Springer released a bunch of free textbooks, but sifting through them kind of sucks. So, I quickly wrote a crawler to grab them and stick them in an index.html file that is slightly easier to work with imo. Make sure that you don't violate any of Springer's rules regarding distributing/storing textbooks. This script is for educational purpose only, and is meant to be an example of how to use python to  quickly download data.


`springer_with_direct_links.csv` contains the columns `pdf_links` which is the link to the raw pdf.  
to  locally download all the pdfs, run `python3 springer_crawl.py`

