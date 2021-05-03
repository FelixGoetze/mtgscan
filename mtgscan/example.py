# %%
from pathlib import Path
from mtgscan.text import MagicRecognition
from mtgscan.ocr.azure import Azure
import streamlit as st
import os
import json
import pandas as pd
from PIL import Image

azure_compute = Azure(
    azure_vision_key=os.environ["AZURE_VISION_KEY"],
    azure_vision_endpoint=os.environ["AZURE_VISION_ENDPOINT"],
)


# %% Card prices from scryfall api
# @st.cache()
# def load_prices():
#     with open("default-cards-20210502210315.json", "r") as read_file:
#         data = json.load(read_file)
#     prices = {}
#     with open("Strixhaven.txt", "a") as the_file:
#         for item in data:
#             if item.get("set_name") == "Strixhaven: School of Mages" or (
#                 item.get("set_name") == "Strixhaven Mystical Archive"
#                 and item.get("lang") == "en"
#             ):
#                 the_file.write(item.get("name").split(" // ")[0] + "$1\n")
#                 # if item.get("set_name") == "Kaldheim":
#                 if item.get("prices").get("usd") is None:
#                     prices[item.get("name").split(" // ")[0]] = float(99)
#                 else:
#                     prices[item.get("name").split(" // ")[0]] = float(
#                         item.get("prices").get("usd")
#                     )
#     with open("prices.txt", "w") as file:
#         file.write(json.dumps(prices))
#     return prices


# prices = load_prices()

# %% card prices from json dictionary
@st.cache()
def load_json_prices():
    with open("prices.txt", "r") as file:
        prices = json.loads(file.read())
    return prices


prices = load_json_prices()
# %% load card names
@st.cache(allow_output_mutation=True)
def load_data():
    rec = MagicRecognition(
        file_all_cards="Strixhaven.txt", file_keywords=Path("Keywords.json")
    )
    return rec


rec = load_data()

# %% Upload File
uploaded_deck = st.file_uploader("Upload a deck", type=["jpg", "jpeg"])

# %% Azure OCR
@st.cache(allow_output_mutation=True)
def azure_ocr(filename):
    box_texts = azure_compute.image_to_box_texts(filename)
    return box_texts


# %% image compression to 4MB https://stackoverflow.com/questions/49124864/how-to-compress-a-picture-less-than-a-limit-file-size-using-python-pil-library


def compress_under_size(size, file_path):
    quality = 90  # not the best value as this usually increases size

    current_size = os.stat(file_path).st_size

    while current_size > size or quality == 0:
        if quality == 0:
            os.remove(file_path)
            print("Error: File cannot be compressed below this size")
            break

        compress_pic(file_path, quality)
        current_size = os.stat(file_path).st_size
        quality -= 5


def compress_pic(file_path, qual):
    """File path is a string to the file to be compressed and
    quality is the quality to be compressed down to"""
    picture = Image.open(file_path)
    dim = picture.size

    picture.save(file_path, "JPEG", optimize=True, quality=qual)

    processed_size = os.stat(file_path).st_size

    return processed_size


# %%

# %% Get Decklist
if uploaded_deck is not None:
    filename = uploaded_deck.name
    # Write uploaded Image to disk
    with open(filename, "wb") as f:
        f.write(uploaded_deck.getbuffer())
    # filename = "deck.jpg"
    # %%
    compress_under_size(4000000, filename)

    # Get OCRed Text from Azure
    box_texts = azure_ocr(filename)
    deck = rec.box_texts_to_deck(box_texts)

    # %% print list with prices
    st.write(f"We found {sum(deck.maindeck.cards.values())} cards")

    prices_dict = {}

    for card in deck.maindeck.cards:
        prices_dict[card] = prices[card]

    ordered_prices = dict(
        sorted(prices_dict.items(), key=lambda item: item[1], reverse=True)
    )

    ordered_prices_df = pd.DataFrame.from_dict(ordered_prices, orient="index")
    st.table(ordered_prices_df)

    # %% show image with boxes too slow
    #!%%time
    box_cards = rec.box_texts_to_cards(box_texts)
    rec._assign_stacked(box_texts, box_cards)

    # %%
    #!%%time
    box_cards.save_image(filename, "image.jpg")
    st.image("image.jpg")

# %%

# %%
