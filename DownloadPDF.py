from bs4 import BeautifulSoup
import re
import os
import recent
import urllib.parse, urllib.request

def getLinks(_soup):
    return [str(link.get('href')) for link in _soup.find_all('a') if '/WPD/MediaReports/' and 'ARREST' in str(link.get('href')).upper()]

if __name__ == "__main__":
    url = 'https://www.wichita.gov/WPD/Pages/PublicRelations.aspx'
    
    with urllib.request.urlopen(url) as response:
        content = response.read()

    soup = BeautifulSoup(content, features='html.parser')
    pdfs = getLinks(soup)

    for i, e in enumerate(pdfs):
        datePattern = '(\d{2}-\d{1,2}-\d{2})'
        match = re.search(datePattern, e)

        file = match[0]
        filename = file + '.pdf'
        locationPDF = 'PDFs/'
        filePDF = locationPDF + filename

        if recent.doesExist(file, locationPDF):
            print(filename + ' already downloaded!')
            continue

        parsedLink = urllib.parse.quote(e)
        url = 'https://www.wichita.gov' + parsedLink
        response = urllib.request.urlopen(url)

        with open(filePDF, 'wb') as f:
            print('Downloading', filename, '...')
            f.write(response.read())
            f.close()
