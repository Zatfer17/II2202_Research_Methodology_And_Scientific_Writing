import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import json

def create_dataset():
    soup = BeautifulSoup(open("../resources/most_sold_games_steam.html", encoding='utf8'), 'html.parser')
    rows = soup.find_all(href=True)

    data_set = []
    tags_set = []
    i=0
    # RegEx for finding tags within the HTML (the div contains multiple blank spaces)
    tag_re = re.compile(r'[\s]{2}([a-zA-Z0-9_]+( [a-zA-Z0-9_]+)*)[\s]{1}')
    for row in rows:
        print("Crawling " + str(i) + " out of " + str(len(rows)))
        if (len(row.contents) == 7):
            link = row.attrs.get("href")
            game = requests.get(link).content
            soup = BeautifulSoup(game, 'html.parser')
            try:
                name = soup.findAll("div", {"class": "apphub_AppName"}).pop().text
                # Retrieve all the tags associated to the game
                tags_matches = tag_re.findall(soup.findAll("div", {"class": "glance_tags popular_tags"}).pop().text)
                # tags_matches contains a list of groups retrieved through the RegEx. We only need the first group of every match
                tags = list(map(lambda elem: elem[0], tags_matches))

                nsfw = False
                banned_tags = ["Sexual Content", "Nudity", "Mature", "Dating Sim", "Gore", "NSFW", "Hentai", "Cute", "Otome"]
                for tag in tags:
                    if tag in banned_tags:
                       nsfw = True
                       break

                dlc = False
                traits = soup.findAll("div", {"class": "game_area_details_specs"})
                for t in traits:
                    if "https://steamstore-a.akamaihd.net/public/images/v6/ico/ico_dlc.png" in str(t):
                        dlc = True

                if not nsfw and not dlc:
                # Build data_set
                    for tag in tags:
                        tags_set.append([tag, 1])
                    data_set.append([name, link, tags])

                i += 1
                """
                For debugging purposes, you may want to stop crawling after a sample X of games
                
                if i == 20:
                    break
                """
            except IndexError:
                continue

    data_df = pd.DataFrame(data_set, columns = ["name", "link", "tags"])
    tags_df = pd.DataFrame(tags_set, columns = ["tag", "popularity"])
    # Print games data to JSON
    data_df.to_json('../resources/games.json', orient='records', indent=2)
    aggregation_functions = {'tag': 'first', 'popularity': 'sum'}
    tags_df = tags_df.groupby('tag', as_index=False).aggregate(aggregation_functions)
    # Sort tags by popularity: most popular tags on top
    tags_df.sort_values("popularity", ascending=False, inplace=True)
    # Print tags data to JSON
    tags_df.to_json('../resources/tags_sorted.json', orient='records', indent=2)

def gather_most_popular():
    data_set = []
    tags_set = []
    tag_re = re.compile(r'[\s]{2}([a-zA-Z0-9_]+( [a-zA-Z0-9_]+)*)[\s]{1}')

    most_popular_df = pd.read_csv("../resources/most_popular_games_steam.csv")

    for link in most_popular_df["link"]:
        game = requests.get(link).content
        soup = BeautifulSoup(game, 'html.parser')
        try:
            name = soup.findAll("div", {"class": "apphub_AppName"}).pop().text
            tags_matches = tag_re.findall(soup.findAll("div", {"class": "glance_tags popular_tags"}).pop().text)
            tags = list(map(lambda elem: elem[0], tags_matches))
            for tag in tags:
                tags_set.append([tag, 1])
            data_set.append([name, link, tags])
        except IndexError:
            continue

    df = pd.DataFrame(data=data_set, columns=["name", "link", "tags"])
    df.to_json("../resources/most_popular_games_steam.json", orient='records')

def purge_nsfw_content():
    banned_tags = ["Sexual Content", "Nudity", "Mature", "Dating Sim", "Gore", "NSFW", "Hentai", "Cute", "Otome"]
    new_data = []
    with open('../resources/games.json') as json_file:
        data = json.load(json_file)
        for d in data:
            nsfw = False
            for t in banned_tags:
                if t in d["tags"]:
                    nsfw = True
                    break
            if not nsfw:
                new_data.append(d)
    with open('../resources/sfw_games.json', 'w') as outfile:
        json.dump(new_data, outfile)

purge_nsfw_content()
