import requests
from bs4 import BeautifulSoup as bs
from lxml.html import fromstring
import datetime
import mysql.connector


def get_proxies():
    # https://www.scrapehero.com/how-to-rotate-proxies-and-ip-addresses-using-python-3/
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

   
def get_matches():
    base_url = f"https://www.mediotiempo.com"

    # Make a get request to get the latest season.
    response = requests.get(f"{base_url}/futbol/liga-mx/calendario")

    # If something goes bad.
    if response.status_code != 200:
        print(f"Something went bad")
        exit()

    # Parse the downloaded html
    soup = bs(response.content, f"html.parser")
    # Get seasons from the dropdown
    seasons_dropdown = soup.find(f"div", {f"class": f"select-seasons"})
    seasons = seasons_dropdown.find_all(type=f"season")

    # For each season in seasons
    for season in seasons:
        # Get the href for the season
        season_url = season.get(f"href")
        full_season_url = f"{base_url}{season_url}"
        
        # Make a request to get phases
        response = requests.get(full_season_url)
        
        # If something goes bad
        if response.status_code != 200:
            print(f"Something went bad with: {full_season_url}")
            continue
        
        # Parse the downloaded html
        soup = bs(response.content, f"html.parser")
        # Get phases from the dropdown
        phases_dropdown = soup.find(f"div", {f"class": f"select-seasonRound"})
        if phases_dropdown is None:
            continue
        phases = phases_dropdown.find_all(type=f"season")
        # For each phase in phases
        for phase in phases:
            # Get the href for the phase
            phase_url = phase.get(f"href")
            full_season_phase_url = f"{base_url}{phase_url}"

            # Make a request to get matchdays
            response = requests.get(full_season_phase_url)

            # If something goes bad
            if response.status_code != 200:
                print(f"Something went bad with: {full_season_phase_url}")
                continue

            # Parse downloaded html
            soup = bs(response.content, f"html.parser")
            # Get matchdays fro the dropdown
            matchdays_dropdown = soup.find(f"div", {f"class": f"select-rounds"})

            # Its regular season
            if type(matchdays_dropdown) is not type(None):
                matchdays = matchdays_dropdown.find_all(type=f"season")
                # For each matchday in matchdays
                for matchday in matchdays:
                    # Get the href for the matchday
                    matchday_url = matchday.get(f"href")
                    full_matchday_url = f"{base_url}{matchday_url}"
                    if matchday_is_in_db(full_matchday_url):
                        continue
                    print(f"Reading {full_matchday_url}")

                    # Make a request to get matches
                    response = requests.get(full_matchday_url)

                    # If something goes bad
                    if response.status_code != 200:
                        print(f"Something went bad with: {full_season_phase_url}")
                        continue

                    # Parse downloaded html
                    parse_matchday(full_matchday_url, bs(response.content, f"html.parser"))
            # Playoffs
            else:
                # Parse the playoff
                if matchday_is_in_db(full_season_phase_url):
                        continue
                print(f"Reading {full_season_phase_url}")
                parse_playoff(full_season_phase_url, bs(response.content, f"html.parser"))


def parse_matchday(url, matchday_html):
    # Get tournament name and year
    seasons_dropdown = matchday_html.find(f"div", {f"class": f"select-seasons"})
    if seasons_dropdown is None:
        return
    tournament_name = seasons_dropdown.find(f"button", {f"class": f"dropbtn"}).text.strip()
    year_array = tournament_name.split(" ")

    if len(year_array) == 2:
        matchday_dropdown = matchday_html.find(f"div", {f"class": f"select-rounds"})
        matchday_name = matchday_dropdown.find(f"button", {f"class": f"dropbtn"}).text.strip()
        matchday_table = matchday_html.find(f"div", {f"class": f"going-container"})
        if matchday_table is None:
            return
        parse_short_tournament(url, tournament_name, int(year_array[1]), matchday_name, matchday_table)
    elif len(year_array) == 3:
        year1 = int(year_array[1])
        year2 = int(year_array[2])
        matchday_dropdown = matchday_html.find(f"div", {f"class": f"select-rounds"})
        matchday_name = matchday_dropdown.find(f"button", {f"class": f"dropbtn"}).text.strip()
        matchday_table = matchday_html.find(f"div", {f"class": f"going-container"})
        if matchday_table is None:
            return
        parse_long_tournament(url, tournament_name, year1, year2, matchday_name, matchday_table)
    return
        

def parse_playoff(url, matchday_html):
    # Get tournament name and year
    seasons_dropdown = matchday_html.find(f"div", {f"class": f"select-seasons"})
    if seasons_dropdown is None:
        return
    tournament_name = seasons_dropdown.find(f"button", {f"class": f"dropbtn"}).text.strip()
    year_array = tournament_name.split(" ")

    if len(year_array) == 2:
        matchday_dropdown = matchday_html.find(f"div", {f"class": f"select-seasonRound"})
        matchday_name = matchday_dropdown.find(f"button", {f"class": f"dropbtn"}).text.strip()
        matchday_table = matchday_html.find(f"div", {f"class": f"going-container"})
        if matchday_table is None:
            return
        parse_short_tournament(url, tournament_name, int(year_array[1]), matchday_name, matchday_table)
        matchday_table = matchday_html.find(f"div", {f"class": f"lap-container"})
        if matchday_table is None:
            return
        parse_short_tournament(url, tournament_name, int(year_array[1]), matchday_name, matchday_table)
    elif len(year_array) == 3:
        year1 = int(year_array[1])
        year2 = int(year_array[2])
        matchday_dropdown = matchday_html.find(f"div", {f"class": f"select-seasonRound"})
        matchday_name = matchday_dropdown.find(f"button", {f"class": f"dropbtn"}).text.strip()
        matchday_table = matchday_html.find(f"div", {f"class": f"going-container"})
        if matchday_table is None:
            return
        parse_long_tournament(url, tournament_name, year1, year2, matchday_name, matchday_table)
        matchday_table = matchday_html.find(f"div", {f"class": f"lap-container"})
        if matchday_table is None:
            return
        parse_long_tournament(url, tournament_name, year1, year2, matchday_name, matchday_table)
    return


def parse_short_tournament(url, tournament_name, year, matchday_name, matchday_table):
    day = None
    month = None
    matchday_date = None
    
    matches = matchday_table.find_all(f"div", {f"class": f"body-going"})
    for match in matches:
        date_html = match.find(f"div", {f"class": f"date"}).find(f"div", {f"class": f"date"})
        date = date_html.text.strip().split(" ")
        date_text = date_html.text.strip()
        if len(date_text) > 0:
            month = get_month_number(date[1])
            day = int(date[0])
            matchday_date = datetime.date(year, month, day)
            today = datetime.date.today()
            if matchday_date > today:
                print(f"{tournament_name} - {matchday_name} have not been played")
                return
        

        result_array = match.find(f"div", {f"class": f"result-team"}).text.split(f"-")
        home_team = match.find(f"div", {f"class": f"first-team"}).find(f"div", {f"class": f"team-name large"}).find(f"a").text
        home_result = result_array[0].strip()
        away_team = match.find(f"div", {f"class": f"second-team"}).find(f"div", {f"class": f"team-name large"}).find(f"a").text
        away_result = result_array[1].strip()
        
        # insert to db
        data = (matchday_date.strftime(f"%Y-%m-%d"), tournament_name, matchday_name, home_team, home_result, away_team, away_result)
        insert_to_db(data)
    insert_matchday_url_to_db(url)


def parse_long_tournament(url, tournament_name, year1, year2, matchday_name, matchday_table):
    year = None
    day = None
    month = None
    matchday_date = None
    
    matches = matchday_table.find_all(f"div", {f"class": f"body-going"})
    for match in matches:
        date_html = match.find(f"div", {f"class": f"date"}).find(f"div", {f"class": f"date"})
        date = date_html.text.strip().split(" ")
        date_text = date_html.text.strip()
        if len(date_text) > 0:
            month = get_month_number(date[1])
            day = int(date[0])
            year = year1 if month > 6 else year2
            matchday_date = datetime.date(year, month, day)
            today = datetime.date.today()
            if matchday_date > today:
                print(f"{tournament_name} - {matchday_name} have not been played")
                return
        

        result_array = match.find(f"div", {f"class": f"result-team"}).text.split(f"-")
        home_team = match.find(f"div", {f"class": f"first-team"}).find(f"div", {f"class": f"team-name large"}).find(f"a").text
        home_result = result_array[0].strip()
        away_team = match.find(f"div", {f"class": f"second-team"}).find(f"div", {f"class": f"team-name large"}).find(f"a").text
        away_result = result_array[1].strip()
        
        # insert to db
        data = (matchday_date.strftime(f"%Y-%m-%d"), tournament_name, matchday_name, home_team, home_result, away_team, away_result)
        insert_to_db(data)
    insert_matchday_url_to_db(url)
    

def get_month_number(month):
    if month == "ENE":
        return 1
    elif month == "FEB":
        return 2
    elif month == "MAR":
        return 3
    elif month == "ABR":
        return 4
    elif month == "MAY":
        return 5
    elif month == "JUN":
        return 6
    elif month == "JUL":
        return 7
    elif month == "AGO":
        return 8
    elif month == "SEP":
        return 9
    elif month == "OCT":
        return 10
    elif month == "NOV":
        return 11
    else:
        return 12


def insert_matchday_url_to_db(url):
    query = f"INSERT INTO ligamx.readed_urls(url) VALUES ('{url}')"
    cnx = mysql.connector.connect(
        user='ligamx_scrapper', 
        password='1234qwer',
        host='localhost',
        database='ligamx')
    cursor = cnx.cursor()
    cursor.execute(query)
    cnx.commit()
    cursor.close()
    cnx.close()


def matchday_is_in_db(url):
    query = f"SELECT url from ligamx.readed_urls WHERE url = '{url}'"
    cnx = mysql.connector.connect(
        user='ligamx_scrapper', 
        password='1234qwer',
        host='localhost',
        database='ligamx')
    cursor = cnx.cursor()
    cursor.execute(query)
    
    flag = False
    for url in cursor:
        print(f"{url} is in db")
        flag = True

    cursor.close()
    cnx.close()
    return flag


def insert_to_db(data):
    print(data)
    query = (
        f"INSERT INTO ligamx.match "
        f"(match_date, tournament_name, match_name, home_team, home_score, away_team, away_score) "
        f"VALUES ('{data[0]}', '{data[1]}', '{data[2]}', '{data[3]}', {data[4]}, '{data[5]}', {data[6]});"
    )
    cnx = mysql.connector.connect(
        user='ligamx_scrapper', 
        password='1234qwer',
        host='localhost',
        database='ligamx')
    cursor = cnx.cursor()
    cursor.execute(query)
    cnx.commit()
    cursor.close()
    cnx.close()
    
    
def main():
    get_matches()
 

if __name__ == f"__main__":
    main()