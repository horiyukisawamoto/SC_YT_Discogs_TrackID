from selenium import webdriver
import pandas as pd
import bs4 as bs
import requests
import time
import numpy as np
import pandas as pd
from datetime import datetime as dt
from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
import re
import xlsxwriter
import pandas.io.formats.excel
from dateutil.relativedelta import relativedelta
import json
import downloader as dl
from dateutil.relativedelta import relativedelta
import datetime
import gargl_google
from selenium.webdriver.firefox.options import Options


class SC_Discogs:

    def __init__(self):

        self.options = Options()
        self.options.headless = True

    def sc_search_artists(self):

        driver = webdriver.Firefox(options=self.options)

        df = pd.read_excel("User_Inputs.xlsx")
        df = df['Artists_To_Search']
        df.dropna(inplace=True)

        track_titles = []
        track_urls = []

        for artist in df:

            if artist != None and pd.isna(artist) == False:

                driver.get('https://soundcloud.com')

                inputElement = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div[2]/div/div/div[2]/div/div[1]/span/span/form/input")))
                inputElement.send_keys(artist)
                inputElement.send_keys(Keys.ENTER)
                time.sleep(0.5)
                inputElement = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div[2]/div/div/div[2]/div/div/div/div/ul/li[2]/a"))).click()

                height = driver.execute_script("return document.body.scrollHeight")

                while height < 30000:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.7)
                    height += driver.execute_script("return document.body.scrollHeight")

                soup = bs.BeautifulSoup(driver.page_source, 'lxml')

                for item in soup.find_all('a', class_='soundTitle__title sc-link-dark'):
                    if artist.lower() in item.text.lower():
                        track_titles.append(item.text.strip())
                        track_urls.append('https://www.soundcloud.com' + item['href'])
                        print('Getting ' + artist + ' : ' + item.text.strip())

        df_artists = pd.DataFrame(zip(track_titles,track_urls),columns=['Mix','MixURL'])

        driver.close()
        driver.quit()

        print('Done with Soundcloud Artists!')

        return df_artists

    def sc_search_pages(self):

        driver = webdriver.Firefox(options=self.options)

        df = pd.read_excel("User_Inputs.xlsx")
        df = df['Artists&Podcast_Pages']
        df.dropna(inplace=True)

        track_titles = []
        track_urls = []

        for page_url in df:

            if page_url != None and pd.isna(page_url) == False:

                driver.get(page_url)

                SCROLL_PAUSE_TIME = 1.7

                # Get scroll height
                last_height = driver.execute_script("return document.body.scrollHeight")

                while True:
                    # Scroll down to bottom
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    # Wait to load page
                    time.sleep(SCROLL_PAUSE_TIME)

                    # Calculate new scroll height and compare with last scroll height
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

                soup = bs.BeautifulSoup(driver.page_source, 'lxml')

                for item in soup.find_all('a', class_='soundTitle__title sc-link-dark'):
                    track_titles.append(item.text.strip())
                    track_urls.append('https://www.soundcloud.com' + item['href'])
                    print('Getting ' + page_url + ' : ' + item.text.strip())

        df_pages = pd.DataFrame(zip(track_titles,track_urls),columns=['Mix','MixURL'])

        driver.close()
        driver.quit()

        print('Done with Soundcloud Pages!')

        return df_pages

    def sc_grab_mixes(self):

        driver = webdriver.Firefox(options=self.options)

        mix_name = []

        df_mixes = pd.read_excel("User_Inputs.xlsx")
        df_mixes = df_mixes['Unique_Mixes']
        df_mixes.dropna(inplace=True)

        for mix_url in df_mixes:

            if mix_url != None and pd.isna(mix_url) == False:

                driver.get(mix_url)

                mix_name.append(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div[2]/div/div[2]/div/div[2]/div[2]/div/div/div[2]/span/span'))).text.strip())

                print('Getting ' + mix_url)

        df_mixes = pd.DataFrame(zip(mix_name,df_mixes),columns=['Mix','MixURL'])

        print('Done with Soundcloud Mixes!')

        return df_mixes

    def concat_3_sc_df(self,df1,df2,df3):

        df_concat_sc = pd.concat([df1,df2,df3],axis=0)

        df_concat_sc.drop_duplicates(inplace=True)

        return df_concat_sc

    def sc_get_comments(self,df):

        driver = webdriver.Firefox(options=self.options)

        mix_name = []
        url_list = []
        comm = []
        comm_time = []

        mix_dict = {k:v for k,v in zip(df['MixURL'],df['Mix'])}

        for url in df['MixURL']:

            try:

                driver.get(url)

                inputElement = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[4]/section/div/div[3]/div[3]/div/div[3]/span[2]")))

                SCROLL_PAUSE_TIME = 1.7

                #exclude tracks that are below 25 mins
                try:
                    if (len(inputElement.text) <= 5 and dt.strptime(inputElement.text, '%M:%S').time() > dt.strptime("25:00", '%M:%S').time()) or len(inputElement.text) > 5:

                        # Get scroll height
                        last_height = driver.execute_script("return document.body.scrollHeight")

                        while True:
                            # Scroll down to bottom
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                            # Wait to load page
                            time.sleep(SCROLL_PAUSE_TIME)

                            # Calculate new scroll height and compare with last scroll height
                            new_height = driver.execute_script("return document.body.scrollHeight")
                            if new_height == last_height:
                                break
                            last_height = new_height

                        soup =  bs.BeautifulSoup(driver.page_source, 'lxml')

                        for x in soup.find_all('div',class_='commentItem__body sc-hyphenate'):
                            if len(x.find_all('a'))>1:
                                comm.append(x.find_all('a')[1].get('title'))
                            else:
                                comm.append(re.sub('\s+',' ', x.text.replace(';','')))

                        for x in soup.find_all('time',class_='relativeTime')[1:]:
                            comm_time.append(dt.strptime(x['datetime'], "%Y-%m-%dT%H:%M:%S.%fZ"))
                            url_list.append(url)
                            mix_name.append(mix_dict.get(url))

                        print('Getting comments for ' + url)

                except:
                    pass

            except (NoSuchElementException, StaleElementReferenceException,TypeError,TimeoutException):
                pass

        df = pd.DataFrame(zip(mix_name,url_list,comm,comm_time),columns=['Mix','MixURL','Comments','Comments Datetime'])

        driver.close()
        driver.quit()

        print('Done getting comments!')

        return df

    def yt_get_comments(self):

        driver = webdriver.Firefox(options=self.options)

        df = pd.read_excel('User_Inputs.xlsx')
        df = df['YT_Artist_Searches']
        df.dropna(inplace=True)

        yt_url = []
        yt_id = []
        yt_title = []
        yt_comments = []
        yt_datetime = []


        for artist in df:

            driver.get("https://www.youtube.com/results?search_query=" + artist + "&sp=CAI%253D")

            driver.execute_script('window.scrollTo(1, 150000);')

            time.sleep(1.5)

            soup = bs.BeautifulSoup(driver.page_source, 'lxml')

            for item in soup.find_all('a', class_='yt-simple-endpoint style-scope ytd-video-renderer'):
                if artist.lower() in item['title'].lower():
                    try:
                        dl.main(['-y'+item['href'].replace('/watch?v=',''),'-oyt_comments.json'])
                        for line in open('yt_comments.json', 'r',encoding='utf-8'):
                            yt_comments.append(json.loads(line.replace(';',""))['text'])
                            yt_datetime.append(json.loads(line.replace(';',""))['time'])
                            yt_url.append('https://www.youtube.com/' + item['href'])
                            yt_title.append(item['title'])

                    except:
                        pass

        df_yt = pd.DataFrame(zip(yt_title,yt_url,yt_comments,yt_datetime),columns=['Mix','MixURL','Comments','Comments Datetime'])

        def transform_yt_datetime(x):
            if any(i in ['年','an','ans','year','years'] for i in x):
                return datetime.date.today() - relativedelta(years=int(re.search(r'\d+', x).group()))
            elif any(i in ['月','mois','month','months'] for i in x):
                return datetime.date.today() - relativedelta(months=int(re.search(r'\d+', x).group()))
            elif any(i in ['週','semaine','semaines','week','weeks'] for i in x):
                return datetime.date.today() - relativedelta(weeks=int(re.search(r'\d+', x).group()))
            elif any(i in ['日','jour','jours','day','days'] for i in x):
                return datetime.date.today() - relativedelta(days=int(re.search(r'\d+', x).group()))
            elif any(i in ['時','heure','heures','hour','hours'] for i in x):
                return datetime.date.today() - relativedelta(hours=int(re.search(r'\d+', x).group()))
            elif any(i in ['分','minute','minutes'] for i in x):
                return datetime.date.today() - relativedelta(minutes=int(re.search(r'\d+', x).group()))
            elif any(i in ['秒','seconde','secondes','heure','heures'] for i in x):
                return datetime.date.today() - relativedelta(seconds=int(re.search(r'\d+', x).group()))
            else:
                x

        df_yt['Comments Datetime'] = df_yt['Comments Datetime'].apply(lambda x : transform_yt_datetime(x))

        driver.close()
        driver.quit()

        return df_yt

    def sc_yt_df_concat(self,df1,df2):

        df_concat_final = pd.concat([df1,df2],axis=0)

        df_concat_final.drop_duplicates(inplace=True)

        df_concat_final.columns = ['SC_Mix/YT_Vid', 'URL','Comment','Comment_Time']

        df_concat_final.dropna(inplace=True)

        df_concat_final.to_csv('df_concat_final.csv',index=False)

    def sc_yt_clean_comments(self):

        df = pd.read_csv('df_concat_final.csv')

        emoji_pattern = re.compile("["
                u"\U0001F600-\U0001F64F"  # emoticons
                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                u"\U0001F680-\U0001F6FF"  # transport & map symbols
                u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                u"\U00002500-\U00002BEF"  # chinese char
                u"\U00002702-\U000027B0"
                u"\U00002702-\U000027B0"
                u"\U000024C2-\U0001F251"
                u"\U0001f926-\U0001f937"
                u"\U00010000-\U0010ffff"
                u"\u2640-\u2642"
                u"\u2600-\u2B55"
                u"\u200d"
                u"\u23cf"
                u"\u23e9"
                u"\u231a"
                u"\ufe0f"  # dingbats
                u"\u3030"
                              "]+", re.UNICODE)

        df['Comment'] = df['Comment'].str.strip()
        df['Comment'] = df['Comment'].apply(lambda x: emoji_pattern.sub("", str(x)))
        df['Comment'] = df['Comment'].apply(lambda x: x.replace(':)','').replace(':D','').replace('<3',''))
        df = df[df['Comment'].apply(lambda x: len(str(x)) > 5)]
        df = df[~df['Comment'].str.contains('id|ID|Id|iD')]
        df['Comment'] = df['Comment'].apply(lambda x: re.sub(r"@.*?:","", str(x)))
        df['Comment'] = df['Comment'].apply(lambda x: re.sub(r"@[A-Za-z0-9]+","", str(x)))
        df['Comment'] = df['Comment'].replace(r'^\s*$', np.nan, regex=True).replace('\n',' ', regex=True)

        df["DiscogsURL"] = "-"

        df.to_csv('df_get_comments.csv',index=False)

        print('Done cleaning comments!')

    def sc_get_discogs_url(self):

        ARG_GTF = 'googlesearch.gtf'

        with open(ARG_GTF, 'r') as conf_file:
            g = gargl_google.gargl(json.load(conf_file))

        df = pd.read_csv('df_get_comments.csv')

        try:
            df_db = pd.read_csv('df_get_comments_discogs.csv')
        except:
            df_db = pd.DataFrame(columns=['SC_Mix/YT_Vid', 'URL','Comment','Comment_Time','DiscogsURL'])

        df_mid = pd.concat([df,df_db],axis=0)
        df_mid = df_mid[df_mid['DiscogsURL']=='-']
        df_mid.drop_duplicates(subset=['SC_Mix/YT_Vid','Comment'],keep=False,inplace=True)
        df_mid.dropna(inplace=True)

        df_mid.to_csv('df_new_added_comments.csv',index=False)

        links_dict = {}

        for count,comment in enumerate(df_mid['Comment'],1):
            try:
                for url in g.Search({'query': comment})[0]['URL']:
                    if 'discogs' in url.get('href'):
                        if ('/release/' or '/master/') in url.get('href'):
                            if '/sell/' not in url.get('href'):
                                links_dict[comment] = re.search('q=(.*)&sa', url.get('href')).group(1)
            except (NoSuchElementException, StaleElementReferenceException,TypeError,TimeoutException) as e:
                print(e)
                print("Error in finding comment number " + str(count) + "'s URL")
                continue

            time.sleep(0.5)

            if count % 10 == 0:
                print(count, 'comments out of', len(df_mid['Comment']),'at:',time.strftime("%d-%m-%Y %H:%M:%S"))

        df_mid['DiscogsURL'] = df_mid['Comment'].apply(lambda x: links_dict.get(x) if links_dict.get(x) is not None else "-")

        df_final = pd.concat([df_db[df_db['DiscogsURL']!='-'],df,df_mid],axis=0)
        df_final.drop_duplicates(inplace=True)

        df_final.to_csv('df_get_comments_discogs.csv',index=False)

        print('Done getting Discogs URLs!')

        return df_final

    def sc_get_discogs_prices(self):

        driver = webdriver.Firefox(options=self.options)

        df = pd.read_csv('df_get_comments_discogs.csv')

        for_sale = []
        last_sold = []
        lowest_sold = []
        median_sold = []
        highest_sold = []
        price_dict= {}

        df = df[df['DiscogsURL']!='-']
        df = df[df['DiscogsURL'].str.contains('https://www.discogs.com')]

        #Instantiate driver once to accept Discogs Cookies & Privacy rules
        driver.get('https://www.discogs.com')
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))).click()

        for count,url in enumerate(df['DiscogsURL'],1):

            try:

                driver.get(url)

                select = Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "i18n_select"))))
                select.select_by_value('en')

                soup = bs.BeautifulSoup(driver.page_source, 'lxml')

                if soup.find_all('span', class_='marketplace_for_sale_count'):
                    for item in soup.find_all('span', class_='marketplace_for_sale_count'):
                        for_sale.append(item.text.strip())
                else:
                    for_sale.append('-')

                if soup.find_all('li', class_='last_sold'):
                    for item in soup.find_all('li', class_='last_sold'):
                        last_sold.append(item.text.split(':')[1].strip())
                else:
                        last_sold.append('-')

                if soup.find_all('ul', class_='last'):
                    for item in soup.find_all('ul', class_='last'):
                        lowest_sold.append(item.find_all('li')[1].text.split(':')[1].strip())
                        median_sold.append(item.find_all('li')[2].text.split(':')[1].strip())
                        highest_sold.append(item.find_all('li')[3].text.split(':')[1].strip())
                else:
                        lowest_sold.append('-')
                        median_sold.append('-')
                        highest_sold.append('-')

            except (NoSuchElementException, StaleElementReferenceException,TypeError,TimeoutException) as e:
                print(e)
                print("Error in finding DiscogsURL " + str(count))
                continue

            if count % 10 == 0:
                print(count, 'DiscogsURL out of', len(df['DiscogsURL']),'at:',time.strftime("%d-%m-%Y %H:%M:%S"))

        df['ForSale'] = for_sale
        df['LastSold'] = last_sold
        df['LowestSold'] = lowest_sold
        df['MedianSold'] = median_sold
        df['HighestSold'] = highest_sold

        df = df.sort_values(by=['Comment_Time'], ascending=False)

        driver.close()
        driver.quit()

        print('Done getting Discogs Prices!')

        return df

    def xls_export(self,df):

        TodaysDate = time.strftime("%d-%m-%Y")

        with pd.ExcelWriter('TrackIDs - ' + TodaysDate + '.xlsx') as writer:

            pandas.io.formats.excel.ExcelFormatter.header_style = None

            df.to_excel(writer,sheet_name='Results',index=False,startrow=0)

            workbook  = writer.book
            worksheet = writer.sheets['Results']

            writer.sheets['Results'].set_zoom(75)

            worksheet.set_column(0, 0, 40)
            worksheet.set_column(1, 9, 20)

            header_format = workbook.add_format({'bold': True,'text_wrap': True,'valign': 'vcenter','fg_color': '#FFBDBD','border': 0, 'font_size':11})

            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

            writer.save()

        print('Excel created!')

if __name__ == '__main__':

    s = SC_Discogs()
    df_sc = s.concat_3_sc_df(s.sc_search_artists(),s.sc_search_pages(),s.sc_grab_mixes())
    df_sc_comments = s.sc_get_comments(df_sc)
    df_yt = s.yt_get_comments()
    df_sc_yt = s.sc_yt_df_concat(df_sc_comments,df_yt)
    clean_final_df = s.sc_yt_clean_comments()
    discogs_url = s.sc_get_discogs_url()
    discogs_price = s.sc_get_discogs_prices()
    s.xls_export(discogs_price)

#rajouter liens bandcamp/junodownload?
