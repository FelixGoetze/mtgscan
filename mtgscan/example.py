# %%
from pathlib import Path
from mtgscan.text import MagicRecognition
from mtgscan.ocr.azure import Azure
import streamlit as st
import os
import json
import pandas as pd

azure_compute = Azure(
    azure_vision_key=os.environ["AZURE_VISION_KEY"],
    azure_vision_endpoint=os.environ["AZURE_VISION_ENDPOINT"],
)

# %% load data

@st.cache()
def load_data():
    rec = MagicRecognition(
        file_all_cards="kaldheim2.txt", file_keywords=Path("Keywords.json")
    )
    return rec

rec = load_data()
# %% Card prices from scryfall api
# # @st.cache()
# def load_prices():
#     with open("default-cards-20210425210323.json", "r") as read_file:
#         data = json.load(read_file)
#     prices = {}
#     for item in data:
#         if item.get("set_name") == "Strixhaven: School of Mages" or item.get("set_name") == "Strixhaven Mystical Archive" :
#             if item.get("prices").get("usd") is None:
#                 prices[item.get("name").split(' // ')[0]] = float(99)
#             else:
#                 prices[item.get("name").split(' // ')[0]] = float(item.get("prices").get("usd"))
#     return prices

# prices = load_prices()

# %% card prices copy pasted from mtggoldfish
df_strix = pd.read_csv('strixhaven.txt', delimiter = "\t", names=["name", "price"])
df_archive = pd.read_csv('mysticalarchive.txt', delimiter = "$", names=["name", "price"])
df_strix['price'] = df_strix['price'].str.replace(',', '').str.replace('$', '').astype(float)
df_archive['price'] = df_archive['price'].astype(float)

df = pd.concat([df_strix, df_archive])
df['name'] = df['name'].str.strip()

# %% Upload File
uploaded_deck = st.file_uploader("Upload a deck", type=["jpg", "jpeg"])

# %% Azure OCR
@st.cache(allow_output_mutation=True)
def azure_ocr(filename):
    box_texts = azure_compute.image_to_box_texts(
        filename
    )
    return box_texts

# %% Get Decklist
if uploaded_deck is not None:
    filename = uploaded_deck.name
# Write uploaded Image to disk
    with open(filename, "wb") as f: 
        f.write(uploaded_deck.getbuffer())
        # filename = "deck.jpg"
        # %%

        # Get OCRed Text from Azure
        box_texts = azure_ocr(filename)
        deck = rec.box_texts_to_deck(box_texts)

        # %% print list with prices
        st.write(f"We found {sum(deck.maindeck.cards.values())} cards")
        st.write("Card prices fetched on DATE from scryfall")

        prices_dict = {}

        for card in deck.maindeck.cards:
            prices_dict[card] = df.loc[df["name"] == card, "price"].item()

        ordered_prices = dict(sorted(prices_dict.items(), key=lambda item: item[1], reverse=True))

        ordered_prices_df = pd.DataFrame.from_dict(ordered_prices, orient = 'index')
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
