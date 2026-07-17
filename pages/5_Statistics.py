import streamlit as st
from sidebar import render_sidebar
from PIL import Image
import os
import base64

# from utils.session_tracker import track_session
# session_count = track_session()

# Page settings
st.set_page_config(
    page_title="Statistics",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_sidebar()

# ---- Horizontal Stats Bar ----
st.markdown("---")
st.markdown(f"""
<div style="display: flex; width: 100%;">
        <div style="flex: 1; background-color: #dadaeb; text-align: center; padding: 20px 0;">
            <h2 style="color:#4a3666; margin-left: 15px;">1595</h2>
            <p style="margin: 0; font-weight: bold; color:#4a3666;">Peptide Entries</p>
        </div>
        <div style="flex: 1; background-color: #eeeeee; text-align: center; padding: 20px 0;">
            <h2 style="color:#4a3666; margin-left: 15px;">31</h2>
            <p style="margin: 0; font-weight: bold; color:#4a3666;">Organisms</p>
        </div>
        <div style="flex: 1; background-color: #dadaeb; text-align: center; padding: 20px 0;">
            <h2 style="color:#4a3666; margin-left: 15px;">76</h2>
            <p style="margin: 0; font-weight: bold; color:#4a3666;">Neuropeptide Families</p>
        </div>
    </div>
""", unsafe_allow_html=True)
st.markdown("---")
# ---- Section: Composition Chart ----
st.markdown("""
<h4 style="margin-bottom: 10px;">1. Family Distribution of Neuropeptides in cNPDB</h4>
""", unsafe_allow_html=True)
image_path = os.path.join("Assets", "Statistics", "Pie Chart Family Distribution.png")
if os.path.exists(image_path):
    st.markdown(f"""
        <div style="margin: 0 auto; text-align: center;">
            <img src="data:image/png;base64,{base64.b64encode(open(image_path, "rb").read()).decode()}" style="width: auto; height: 400px;" />
        </div>
    """, unsafe_allow_html=True)
else:
    st.error(f"Image not found at {image_path}")

st.markdown("""
<h4 style="margin-top: 40px; margin-bottom: 10px;">2. Composition of Neuropeptides per Organism in cNPDB</h4>
""", unsafe_allow_html=True)
image_path = os.path.join("Assets", "Statistics", "Pie Chart Organism Distribution.png")
if os.path.exists(image_path):
    st.markdown(f"""
        <div style="margin: 0 auto; text-align: center;">
            <img src="data:image/png;base64,{base64.b64encode(open(image_path, "rb").read()).decode()}" style="width: auto; height: 400px;" />
        </div>
    """, unsafe_allow_html=True)
else:
    st.error(f"Image not found at {image_path}")

st.markdown("""
<h4 style="margin-top: 40px; margin-bottom: 10px;">3. Composition of Neuropeptides per Physiological and Biological Studies in cNPDB</h4>
""", unsafe_allow_html=True)
image_path = os.path.join("Assets", "Statistics", "Pie chart Biological Application.png")
if os.path.exists(image_path):
    st.markdown(f"""
        <div style="margin: 0 auto; text-align: center;">
            <img src="data:image/png;base64,{base64.b64encode(open(image_path, "rb").read()).decode()}" style="width: auto; height: 400px;" />
        </div>
    """, unsafe_allow_html=True)
else:
    st.error(f"Image not found at {image_path}")

st.markdown("""
<h4 style="margin-top: 40px; margin-bottom: 10px;">4. Composition of Neuropeptides per Investigation Techniques in cNPDB</h4>
""", unsafe_allow_html=True)
image_path = os.path.join("Assets", "Statistics", "Pie chart Technique.png")
if os.path.exists(image_path):
    st.markdown(f"""
        <div style="margin: 0 auto; text-align: center;">
            <img src="data:image/png;base64,{base64.b64encode(open(image_path, "rb").read()).decode()}" style="width: auto; height: 400px;" />
        </div>
    """, unsafe_allow_html=True)
else:
    st.error(f"Image not found at {image_path}")



st.markdown("""
<h4 style="margin-top: 40px; margin-bottom: 10px;">5. Properties of All Peptides in cNPDB</h4>
""", unsafe_allow_html=True)
image_path = os.path.join("Assets", "Statistics", "Peptide Property Violin.png")
if os.path.exists(image_path):
    st.markdown(f"""
        <div style="margin: 0 auto; text-align: center;">
            <img src="data:image/png;base64,{base64.b64encode(open(image_path, "rb").read()).decode()}" style="width: auto; height: 600px;" />
        </div>
    """, unsafe_allow_html=True)
else:
    st.error(f"Image not found at {image_path}")

st.markdown("""
<h4 style="margin-top: 40px; margin-bottom: 10px;">6. Distribution of Existence Evidence for All Peptides in cNPDB</h4>
""", unsafe_allow_html=True)
image_path = os.path.join("Assets", "Statistics", "Pie Chart Existence Distribution.png")
if os.path.exists(image_path):
    st.markdown(f"""
        <div style="margin: 0 auto; text-align: center;">
            <img src="data:image/png;base64,{base64.b64encode(open(image_path, "rb").read()).decode()}" style="width: auto; height: 400px;" />
        </div>
    """, unsafe_allow_html=True)
else:
    st.error(f"Image not found at {image_path}")

st.markdown("""
<h4 style="margin-top: 40px; margin-bottom: 10px;">7. Amino Acids Composition from All Peptides in cNPDB</h4>
""", unsafe_allow_html=True)
image_path = os.path.join("Assets", "Statistics", "Amino Acid Composition.png")
if os.path.exists(image_path):
    st.markdown(f"""
        <div style="margin: 0 auto; text-align: center;">
            <img src="data:image/png;base64,{base64.b64encode(open(image_path, "rb").read()).decode()}" style="width: auto; height: 400px;" />
        </div>
    """, unsafe_allow_html=True)
else:
    st.error(f"Image not found at {image_path}")


st.markdown("""
<div style="text-align: center; font-size:14px; color:#2a2541;">
  <em>Last update: Jul 2026</em>
</div>
""", unsafe_allow_html=True)

