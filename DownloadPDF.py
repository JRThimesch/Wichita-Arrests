from bs4 import BeautifulSoup
import re
import os
import recent
import urllib.parse, urllib.request

if __name__ == "__main__":
    pdfs = []
    url = 'https://www.wichita.gov/WPD/Pages/PublicRelations.aspx'
    
    with urllib.request.urlopen(url) as response:
        content = response.read()

    soup = BeautifulSoup(content, features='html.parser')
    
    with open('html.txt', 'w', encoding="utf-8") as html:
        for link in soup.find_all('a'):
            strLink = str(link.get('href'))
            strLinkUpper = strLink.upper()
            if '/WPD/MediaReports/' and 'ARREST' in strLinkUpper:
                html.write('https://www.wichita.gov' + strLink + '\n')
                pdfs.append(strLink)

    for i, e in enumerate(pdfs):
        datePattern = '(\d{2}-\d{1,2}-\d{2})'
        match = re.search(datePattern, e)
        filename = match[0] + '.pdf'

        if recent.doesExist(filename, '.pdf'):
            print(filename + ' already downloaded!')
            continue

        parsed = urllib.parse.quote(e)
        url = 'https://www.wichita.gov' + parsed
        response = urllib.request.urlopen(url)

        with open(filename, 'wb') as file:
            print('Downloading', filename, '...')
            file.write(response.read())
            file.close()
