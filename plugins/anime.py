# copyright 2024 © KavinduAJ | https://github.com/kjeymax


from pyrogram import Client, filters
from pyrogram.types import Message
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Define the path to the watermark image
WATERMARK_PATH ="/content/Auto-Filter-Bot/anilist_watermark.png"

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

    # title
    title1 = title.get("english")
    title2 = title.get("romaji")

    if title2 is None:
        title2 = title.get("native")

    if title1 is None:
        title1 = title2

    # genre

    genre = ", ".join(genres)

    caption = """
📺 **{}** **({})**\n

╭🎭 Genre : `{}`
├🧬 Type : `{}`
├📡 Status : `{}`
├🗓 Episodes : `{}`
├💾 Duration : `{}`
├⭐️ Rating : `{}/100`
├🎞 Format : `4K/FHD`
├☁️ Source » `HD Cloud`
╰📤 Upload »  @h_donghua
""".format(
        title1, title2, genre, form, status, episodes, duration, averageScore
    )

    if trailer:
        ytid = trailer.get("id")
        site = trailer.get("site")
    else:
        site = None

    if site == "youtube":
        caption += "\n[Trailer](https://www.youtube.com/watch?v={}) | [More Info](https://anilist.co/anime/{})".format(
            ytid, id_
        )
    else:
        caption += "\n[More Info](https://anilist.co/anime/{})".format(id_)
     

    return img, caption

def add_watermark(image_url):
    # Download the image from the URL
    response = requests.get(image_url)
    if response.status_code != 200:
        # Handle error if the image couldn't be downloaded
        return None

    # Open the downloaded image from the response content
    poster = Image.open(BytesIO(response.content))
    
    # Open the watermark image
    watermark = Image.open(WATERMARK_PATH)

    # Resize watermark image to fit the poster
    watermark_width = int(poster.width * 0.25)
    watermark_height = int((watermark_width / watermark.width) * watermark.height)
    watermark = watermark.resize((watermark_width, watermark_height))
    
    # Paste the watermark onto the poster image
    offset = (poster.width - watermark.width, poster.height - watermark.height)
    poster.paste(watermark, offset, watermark)
    return poster

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
        # Add watermark to the anime poster
        img_with_watermark = add_watermark(img_url)
        if img_with_watermark:
            # Send the anime information as a message with the watermarked image
            bio = BytesIO()
            bio.name = 'image.jpeg'
            img_with_watermark = img_with_watermark.convert("RGB")
            img_with_watermark.save(bio, "JPEG")
            bio.seek(0)
            await message.reply_photo(photo=bio, caption=caption)
        else:
            await message.reply_text("Error adding watermark to the anime poster.")
    else:
        await message.reply_text("Anime not found or error occurred.")
