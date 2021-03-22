# %%
from pathlib import Path
from mtgscan.text import MagicRecognition
from mtgscan.ocr.azure import Azure
import streamlit as st
import os


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


# %%
rec = load_data()

# %%
# st.write("Upload a deck")
uploaeded_deck = st.file_uploader("Upload a deck", type=["jpg", "jpeg"])


# %%

if uploaeded_deck is not None:
    with open("deck.jpg", "wb") as f:
        f.write(uploaeded_deck.getbuffer())
    box_texts = azure_compute.image_to_box_texts(
        "deck.jpg"
        # "https://user-images.githubusercontent.com/49362475/105632710-fa07a180-5e54-11eb-91bb-c4710ef8168f.jpeg"
    )
    deck = rec.box_texts_to_deck(box_texts)
    print(deck)
    st.write(deck)

    # %%
    box_cards = rec.box_texts_to_cards(box_texts)
    rec._assign_stacked(box_texts, box_cards)
    box_cards.save_image("EwjawBtVkAA1T2_.jpeg", "image.jpg")
    st.image("image.jpg")

# %%
