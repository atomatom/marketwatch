#!/usr/local/bin/python3
'''
- to use Google Drive Spreadsheet as database -
https://console.developers.google.com/
    - enable Google Drive API, Google Sheets API
https://github.com/burnash/gspread
http://gspread.readthedocs.io/en/latest/oauth2.html

pip install gspread     ## library package to use Google Spreadsheets
pip install oauth2client    ## to authorize with Google Drive API
                            # using OAuth 2.0

- base requirements -
pip install bs4     ## installs webscrape library package
pip install lxml    ## install webscrape lexicon for parsing
(pip install html5lib)  ## optionalL installs second parsing lexicon
pip install requests    ## installs request library for http commands
pip list            ## display your installed packages
'''

from bs4 import BeautifulSoup
import requests
import csv

import sys
print(sys.executable)
print(sys.version)
print(sys.argv[0])
print()

print('=' * 40)


import gspread
from oauth2client.service_account import ServiceAccountCredentials
# import pprint

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('marketwatch_report_client.json', scope)
client = gspread.authorize(creds)

# Find a Google Sheet workbook by name and open the first sheet
sheet = client.open("MarketWatch Report").sheet1
sheet.clear()

sheet_header_row = ['Ticker',
                    'Price',
                    'Daily Change',
                    'Daily Percent',
                    'YTD',
                    '1 Year',
                    '5 Year',
                    'Last Updated',
                    'Company',
                    'Source',
                    ]

sheet.append_row(sheet_header_row)

csv_file = open('marketwatch_report.csv', 'w', encoding='utf-8')

csv_writer = csv.writer(csv_file)
csv_writer.writerow(sheet_header_row)

marketwatch_urlbase = 'https://www.marketwatch.com/investing/'

ticker_stocks = {
    'amzn': 'stock', 'nvda': 'stock', 'aapl': 'stock',
    'goog': 'stock', 'fb': 'stock', 'mu': 'stock',
    'nflx': 'stock', 'mchp': 'stock', 'stt': 'stock',
    'dow': 'stock', 'nasdaq': 'stock', 'sp500': 'stock',
}

ticker_funds = {
    'fgckx': 'fund', 'rairx': 'fund', 'prjpx': 'fund',
}

ticker = {**ticker_stocks, **ticker_funds}

for symbol in sorted(ticker.keys()):
    # print(symbol)
    marketwatch_url = marketwatch_urlbase + ticker[symbol] + '/' + symbol
    source = requests.get(marketwatch_url).text

    soup = BeautifulSoup(source, 'lxml')

    print(soup.title.text)
    print()

    intraday_element = soup.find('div', class_='element element--intraday')

    company_ticker = intraday_element.find('span', class_='company__ticker').text
    company_market = intraday_element.find('span', class_='company__market').text
    print(f'{company_ticker}, {company_market}')

    intraday_price = intraday_element.find('h3', class_='intraday__price').text
    intraday_price = ''.join(intraday_price.split())

    change_point = intraday_element.find('span', class_='change--point--q').text
    change_percent = intraday_element.find('span', class_='change--percent--q').text

    print(f'{intraday_price} ({change_point}, {change_percent})')

    volume = intraday_element.find('div', class_='intraday__volume')
    if volume:
        print(" ".join(volume.text.split('\n')) + '\n')

    timestamp = intraday_element.find('span', class_='timestamp__time').text
    timestamp = timestamp.split(': ')[1]
    print(timestamp)
    timetype = intraday_element.find('small', class_='timestamp__type')
    if timetype:
        print(timetype.text)

    print()

    keydatalist_element = soup.find('div', class_='element element--list')

    keydata_title = keydatalist_element.h2.text.strip()
    # print(keydata_title)

    keydata = {}
    keydata_item = keydatalist_element.find_all('li', class_='kv__item')
    for i in keydata_item:
        item = i.text.strip().split('\n')
        key = item[0]
        value = item[1:]
        keydata.__setitem__(key, value)

    # for n, (k, v) in enumerate(keydata.items()):
    #     print(f'{n+1}. {k}: {v}')

    if ticker[symbol] == 'fund':
        YTD = keydata.get('YTD', 'none')[0]
        Return_5year = keydata.get('5 Year', 'none')[0]
        Return_1year = keydata.get('52 Week Avg Return', 'none')[0]

    # print()

    if ticker[symbol] == 'stock':
        performance_element = soup.find('div', class_='element element--table performance')

        perf_title = performance_element.h2.text.strip()
        # print(perf_title)

        perfdata = {}
        perf_timeresult = performance_element.find_all('tr', class_='table__row')
        for i in perf_timeresult:
            perf_time = i.td.text if i.td else 'None'
            perf_result = i.li.text if i.li else 'None'
            # print(f'{perf_time}, {perf_result}')
            perfdata.__setitem__(perf_time, perf_result)

        # for n, (k, v) in enumerate(perfdata.items()):
        #     print(f'{n+1}. {k}: {v}')

        YTD = perfdata.get('YTD', 'none')
        Return_1year = perfdata.get('1 Year', 'none')
        Return_5year = 'none'

    print('=' * 40)

    Company = soup.title.text.split(' - ')[1]
    Clickable_Link = '<a href=\"' + marketwatch_url + '\"">' + Company + '</a>'

    data = [company_ticker,
            intraday_price,
            change_point,
            change_percent,
            YTD,
            Return_1year,
            Return_5year,
            timestamp,
            # Clickable_Link,
            Company,
            marketwatch_url,
            ]

    sheet.append_row(data)

    csv_writer.writerow(data)


csv_file.close()
