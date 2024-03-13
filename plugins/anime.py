from pyrogram import Client, filters
from pyrogram.types import Message
import requests

ANIME_QUERY = """
query ($id: Int, $idMal:Int, $search: String) {
  Media (id: $id, idMal: $idMal, search: $search, type: ANIME) {
    id
    idMal
    title {
      romaji
      english
      native
    }
    format
    status
    episodes
    duration
    countryOfOrigin
    source (version: 2)
    trailer {
      id
      site
    }
    genres
    tags {
      name
    }
    averageScore
    producers {
      nodes {
        name
      }
    }
    source
    startDate {
      year
      month
      day
    }
    native
    relations {
      edges {
        node {
          title {
            romaji
            english
          }
          id
        }
        relationType
      }
    }
    nextAiringEpisode {
      timeUntilAiring
      episode
    }
    isAdult
    isFavourite
    mediaListEntry {
      status
      score
      id
    }
    siteUrl
  }
}
"""


ANIME_DB = {}


def return_json_senpai(query: str, vars_: dict):
    url = "https://graphql.anilist.co"
    anime = vars_["search"]
    db = ANIME_DB.get(anime)

    if db:
        return db

    data = requests.post(url, json={"query": query, "variables": vars_}).json()
    ANIME_DB[anime] = data

    return data


def get_anime(vars_, less):
    result = return_json_senpai(ANIME_QUERY, vars_)

    error = result.get("errors")
    if error:
        error_sts = error[0].get("message")
        print(f"[{error_sts}]")
        print(vars_)
        return None

    data = result["data"]["Media"]
    idm = data.get("id")
    title = data.get("title")
    tit = title.get("english")
    if tit is None:
        tit = title.get("romaji")

    tit = format_text(tit)
    title_img = f"https://img.anili.st/media/{idm}"

    if less:
        return idm, title_img, tit

    return data


def format_text(text):
    # Implement your formatting logic here
    return text


def get_anime_name(title):
    x = title.split(" - ")[-1]
    x = title.replace(x, "").replace("-", "").strip()
    x = x.split(" ")
    x = x[:4]
    y = ""
    for i in x:
        y += i + " "
    return y


def get_anilist_data(name):
    vars_ = {"search": name}
    data = get_anime(vars_, less=False)

    if not data:
        return None

    id_ = data.get("id")
    title = data.get("title")
    form = data.get("format")
    status = data.get("status")
    episodes = data.get("episodes")
    duration = data.get("duration")
    trailer = data.get("trailer")
    genres = data.get("genres")
    averageScore = data.get("averageScore")
    img = f"https://img.anili.st/media/{id_}"
    producers = data.get("producers")
    source = data.get("source")
    native_title = title.get("native")
    start_date = data.get("startDate")

    # title
    title1 = title.get("english")
    title2 = title.get("romaji")

    if title2 is None:
        title2 = native_title

    if title1 is None:
        title1 = title2

    # genre

    genre = ", ".join(genres)
    producers_str = ", ".join(producer.get("name") for producer in producers) if producers else "Unknown"

    caption = """
📺 **{}**
  ({})
🎭 Genre : `{}`
🧬 Type : `{}`
📡 Status : `{}`
🗓 Episodes : `{}`
💾 Duration : `{}`
⭐️ Rating : `{}/100`
🎬 Producers : `{}`
🔖 Source : `{}`
🔠 Native : `{}`
📅 Start Date : `{}`
""".format(
        title1, title2, genre, form, status, episodes, duration, averageScore, producers_str, source, native_title, start_date
    )

    if trailer:
        ytid = trailer.get("id")
        site = trailer.get("site")
    else:
        site = None

    if site == "youtube":
        caption += "\n[HD FanSUB](https://t.me/h_donghua) | [Trailer](https://www.youtube.com/watch?v={}) | [More Info](https://anilist.co/anime/{})".format(
            ytid, id_
        )
    else:
        caption += "\n[More Info](https://anilist.co/anime/{})".format(id_)
     

    return img, caption


# Define a handler function for the /anime command
@Client.on_message(filters.command('anime'))
async def anime_command(client, message: Message):
    # Extract the anime name from the message
    command = message.text.split(" ", 1)
    if len(command) != 2:
        await message.reply_text("Please provide the name or id of the anime.")
        return

    anime_name = command[1]

    # Call get_anilist_data to retrieve anime information
    result = get_anilist_data(anime_name)

    # Check if data is retrieved successfully
    if result:
        img_url, caption = result
        # Send the anime information as a message with an image
        await message.reply_photo(photo=img_url, caption=caption)
    else:
        await message.reply_text("Anime not found or error occurred.")
