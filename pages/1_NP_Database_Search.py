import streamlit as st
from sidebar import render_sidebar
import pandas as pd
import os
from PIL import Image
import base64
import re
import numpy as np
import streamlit.components.v1 as components
import io
import zipfile
import mimetypes

# from utils.session_tracker import track_session
# track_session()


st.set_page_config(
    page_title="NP Database search",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_sidebar()

st.markdown(
    """
    <style>
      /* Prevent horizontal scroll */
      body, .main, .block-container {
        overflow-x: hidden !important;
      }

      /* Limit max width of the entire interface */
      .main-search-container {
        max-width: 100vw;
        overflow-x: hidden;
      }
      
      /* Make first column auto-size to its content */
      .peptide-details table {
        width: 100%;
        table-layout: auto;
        border-collapse: separate !important;
        border-spacing: 0 3px !important;
      }
    
      .peptide-details table {
        width: 100%;
        table-layout: auto;
        border-collapse: separate !important;
        border-spacing: 0 3px !important;
        margin-top:10px;
      }  
      .peptide-details td:first-child {
        white-space: nowrap;
        width: 1%;
        color: white;
      }
      .peptide-details td:last-child {
        background-color: white;
        word-wrap: break-word;
        overflow-wrap: anywhere;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def read_structure_file(file_path: str) -> str:
    # Read a structure file from disk and cache the contents.
    with open(file_path, 'r') as f:
        return f.read()
        
def show_structure_cif(cif_path, width=350, height=250):
    import py3Dmol
    # Use cached file read instead of raw open()
    cif_data = read_structure_file(cif_path)
    # set up the viewer
    view = py3Dmol.view(width=width, height=height)
    view.addModel(cif_data, 'cif')
    # Set cartoon style using B-factor as color (pLDDT scores)
    view.setStyle({'cartoon': {
        'colorfunc': 'b',
        'colorscheme': {
            'prop': 'b',
            'gradient': 'roygb',
            'min': 0,
            'max': 100
        }
    }})
    view.zoomTo()
    # embed it
    html = view._make_html()
    components.html(html, height=height)


def show_structure_pdb(pdb_path, width=350, height=250):
    import py3Dmol
    # Use cached file read instead of raw open()
    pdb_data = read_structure_file(pdb_path)
    
    # Set up the 3Dmol viewer
    view = py3Dmol.view(width=width, height=height)
    view.addModel(pdb_data, 'pdb')  # specify it's a PDB model
    
    # Use B-factor for coloring if it stores pLDDT (AlphaFold-style)
    view.setStyle({'cartoon': {
        'colorfunc': 'b',
        'colorscheme': {
            'prop': 'b',
            'gradient': 'roygb',
            'min': 0,
            'max': 1
        }
    }})
    view.zoomTo()
    
    # Render the HTML and display it in Streamlit
    html = view._make_html()
    components.html(html, height=height)

import requests
import hashlib

ESMFOLD_API_URL = "https://api.esmatlas.com/foldSequence/v1/pdb/"
ESM_CACHE_DIR = "Assets/3D Structure ESMFold_cache"
os.makedirs(ESM_CACHE_DIR, exist_ok=True)

@st.cache_data(show_spinner=False)
def fetch_esmfold_pdb_path(raw_sequence: str):
    """
    Ensure a cached PDB exists for this raw sequence (calls the ESMFold API
    only once per unique peptide, ever) and return its local path, or None.
    """
    seq = re.sub(r'[^A-Za-z]', '', str(raw_sequence)).upper()
    if not seq or len(seq) > 400:
        return None
    cache_key = hashlib.md5(seq.encode()).hexdigest()
    cache_path = os.path.join(ESM_CACHE_DIR, f"{cache_key}.pdb")
    if os.path.exists(cache_path):
        return cache_path
    try:
        resp = requests.post(ESMFOLD_API_URL, data=seq, timeout=60)
        resp.raise_for_status()
        with open(cache_path, "w") as f:
            f.write(resp.text)
        return cache_path
    except requests.RequestException:
        return None

def img_html(path):
    """Return a base64 <img> tag filling 100% width of its container."""   
    if not os.path.exists(path):
        return "<div style='color:#999; padding:20px;'>No image found</div>"
    ext = os.path.splitext(path)[1].lower().replace(".", "")
    mime = f"image/{'jpeg' if ext in ('jpg','jpeg') else ext}"
    data = base64.b64encode(open(path, "rb").read()).decode()
    return f"<img src='data:{mime};base64,{data}' style='width:100%; height:auto;'/>"

# Helper to blank out NaNs if there is no value in the cell of the column of excel file
def disp(val):
    """Return an empty string if val is NaN/None, else val itself."""
    if pd.isna(val) or val is None:
        return ""
    return val

def display_peptide_details(row: pd.Series):
    active_seq = row["Active Sequence"]
    cNPDB_id    = int(row["cNPDB ID"])

# Prepare all content as HTML strings first
    # 1) Metadata table
    gravy = row.get("GRAVY")
    gravy_str = f"{gravy:.2f}" if pd.notna(gravy) else ""

    metadata_html = f"""
    <div class="peptide-details">
        <table>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">cNPDB ID</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(int(row["cNPDB ID"]))}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Family</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['Family'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Organisms</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2;; border-radius: 0 10px 10px 0; ">{disp(row['OS'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Tissue</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['Tissue'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Existence</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['Existence'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Mass (Da)</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['Mass (Da)'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Length (a.a.)</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['Length'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">GRAVY Score</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{gravy_str}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">% Hydrophobic Residue</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['% Hydrophobic Residue'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Instability Index </td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['Instability Index'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Isoelectric Point (pI) </td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['Isoelectric Point (pI)'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Net Charge (pH 7.0)</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['Net Charge (pH 7.0)'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Aliphatic Index</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['Aliphatic Index'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Boman Index</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['Boman Index'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">PTM</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['PTM'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Physiological Studies</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['Topic'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Instrument</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['Instrument'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">Technique</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['Technique'])}</td>
            </tr>
            <tr>
            <td style="background-color:#6a51a3; color:white; padding:4px 8px; line-height:1.2; border-radius: 10px 0 0 10px; ">DOI</td>
            <td style="background-color:white; border:1px solid #6A0DAD; padding:4px 8px; line-height:1.2; border-radius: 0 10px 10px 0; ">{disp(row['DOI'])}</td>
            </tr>
        </table>
    </div>
    """
     # — Prepare MSI HTML blocks —
    msi_blocks = []
    for tissue_col, asset_folder in [
        ("MSI Tissue 1", "Assets/MSImaging"),
        ("MSI Tissue 2", "Assets/MSImaging"),
        ("MSI Tissue 3", "Assets/MSImaging"),
    ]:
        tissue = disp(row.get(tissue_col))
        if not tissue:
            continue  # Skip if tissue info is missing
    
        suffix = " " + tissue_col.split()[-1]
        jpeg_path = f"{asset_folder}/MSI cNP{cNPDB_id}{suffix}.jpeg"
    
        if not os.path.exists(jpeg_path):
            continue  # Skip if image not found
            
        # Encode image as base64 for download
        with open(jpeg_path, "rb") as f:
            img_bytes = f.read()
            img_base64 = base64.b64encode(img_bytes).decode()
            mime = mimetypes.guess_type(jpeg_path)[0] or "image/jpeg"
    
        # Create block with image preview + downloadable base64 link
        block = f"""
        <div style="color:#6a51a3; font-size:16px; font-weight:bold; text-align:center; margin-bottom:5px;">
          Mass Spectrometry Imaging – {tissue}
        </div>
        <div style="border:2px dashed #6a51a3; padding:10px; margin-bottom:10px; text-align:center;">
          {img_html(jpeg_path)}
        </div>
        <div style="text-align:center; margin-bottom:30px;">
          <a download="MSI cNP{cNPDB_id}{suffix}.jpeg"
             href="data:{mime};base64,{img_base64}"
             style="
               display:inline-block;
               padding:10px 20px;
               background-color:#6a51a3;
               color:white;
               font-weight:bold;
               text-decoration:none;
               border-radius:8px;
               box-shadow: 2px 2px 4px rgba(0,0,0,0.2);
             ">
            Download Peptide's MSI Image
          </a>
        </div>
        """
        msi_blocks.append(block)
    
    # Fallback if no MSI data available
    if not msi_blocks:
        msi_blocks.append("""
        <div style="text-align:center; color:#888; font-style:italic; margin-top:20px;">
          No MSI data is available for this peptide.
        </div>
        """)

    # — Now lay out in three real Streamlit columns —
    st.markdown(
      f"<h3 style='text-align:center;color:#6a51a3;padding-bottom:10px;'>{active_seq}</h3>",
      unsafe_allow_html=True
    )
    col_meta, col_struct, col_msi = st.columns([4,3,3])

    with col_meta:
        st.markdown(metadata_html, unsafe_allow_html=True)

    with col_struct:
        st.markdown(
          "<div style='text-align:center;font-weight:bold;color:#6a51a3;'>AlphaFold-predicted 3D Structure</div>",
          unsafe_allow_html=True
        )

        if cNPDB_id <= 1000:
            folder = "Assets/3D Structure AlphaFold 1_1000"
        else:
            folder = "Assets/3D Structure AlphaFold 1001_2000"
        
        cif_file = os.path.join(folder, f"3D cNP {cNPDB_id}.cif")
        if os.path.exists(cif_file):
            show_structure_cif(cif_file, width=350, height=250)
            # Add download button right below 3D view
            with open(cif_file, "rb") as f:
                cif_bytes = f.read()
                cif_base64 = base64.b64encode(cif_bytes).decode()

            st.markdown(
                f"""
                <div style="text-align:center; margin-top:15px;">
                  <a download="3D_cNP {cNPDB_id}.cif"
                     href="data:chemical/x-cif;base64,{cif_base64}"
                     style="
                       display:inline-block;
                       padding:10px 20px;
                       background-color:#6a51a3;
                       color:white;
                       font-weight:bold;
                       text-decoration:none;
                       border-radius:8px;
                       box-shadow: 2px 2px 4px rgba(0,0,0,0.2);
                     ">
                    Download AlphaFold 3D Structure
                  </a>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.write("No AlphaFold-predicted 3D structure are available for this peptide")

         # Meta PDB file
        meta_pdb_file = fetch_esmfold_pdb_path(row["Sequence"])
        if meta_pdb_file:
            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<div style='text-align:center;font-weight:bold;color:#6a51a3;'>ESMFold-predicted 3D Structure</div>",
                unsafe_allow_html=True
            )
        
            show_structure_pdb(meta_pdb_file, width=350, height=250)
        
            # Download button for PDB
            with open(meta_pdb_file, "rb") as f:
                pdb_bytes = f.read()
                pdb_base64 = base64.b64encode(pdb_bytes).decode()
        
            st.markdown(
                f"""
                <div style="text-align:center; margin-top:10px;">
                  <a download="3D_Meta_cNP{cNPDB_id}.pdb"
                     href="data:chemical/x-pdb;base64,{pdb_base64}"
                     style="
                       display:inline-block;
                       padding:8px 16px;
                       background-color:#6a51a3;
                       color:white;
                       font-weight:bold;
                       text-decoration:none;
                       border-radius:6px;
                       box-shadow: 2px 2px 4px rgba(0,0,0,0.2);
                     ">
                    Download ESMfold 3D Structure
                  </a>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.write("No ESMFold-predicted 3D structure is available for this peptide.")
            
    with col_msi:
        for block in msi_blocks:
            st.markdown(block, unsafe_allow_html=True)

st.markdown("""
<style>
/* Centered title */
 h2.custom-title {
    text-align: center !important;
    margin-top: 10px !important;
    color: #29004c;
 }
 
 /* Section titles */
  .section-title {
    color: #6a51a3;
    font-size: 16px;
    font-weight: bold;
  }
  /* Checkbox accent color */
  input[type="checkbox"] { accent-color: #6a51a3; }
  
    /* Adjusting space for sliders in col_filter */
  .stSlider { 
      margin-top: 5px;
      margin-bottom: 9px;
   }
   
   /* Custom columns layout: 20px gap between filter and main */
    .custom-col-container {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        max-width: 100%;
        overflow-x: hidden;
    }
    
    /* Force equal height by filling both columns */
    .fill-height {
        flex: 1;
    }

    /* Reduce space between checkboxes */
div.stCheckbox {
    margin-top: -5px;  /* adjust to your preference */
    margin-bottom: 0px;
    }
</style>
""", unsafe_allow_html=True)

# --- Load Data ---
@st.cache_data
def load_database():
    return pd.read_parquet("Assets/20260418_cNPDB.parquet")

df = load_database()

# --- FASTA DOWNLOAD: Full Database ---
@st.cache_data
def build_full_fasta(_df):
    return "\n".join(
        f">{str(row['ID']).lstrip('>')}\n{str(row['Sequence'])}"
        for _, row in _df.iterrows()
        if pd.notna(row['ID']) and pd.notna(row['Sequence'])
    )

full_fasta = build_full_fasta(df)

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.download_button(
        label="Download Full cNPDB Database (FASTA)",
        data=full_fasta,
        file_name="cNPDB_Full_Database.fasta",
        mime="text/plain",
        type="primary",
        key="download_full_fasta"
    )

# --- Separator Line ---
st.markdown("""
<hr style='border: none; border-top: 2px solid #6a51a3; margin: 0px 30px;'>
""", unsafe_allow_html=True)

# --- Centered, spaced title ---
st.markdown(
    '<h2 class="custom-title">'
    'NEUROPEPTIDE SEARCH'
    '</h2>',
    unsafe_allow_html=True
)

# Begin styled container
st.markdown('<div class="main-search-container">', unsafe_allow_html=True)

# Ensure numeric columns are numeric
numeric_cols = ['Mass (Da)', 'Length', 'GRAVY', '% Hydrophobic Residue', 'Instability Index Value', 'Isoelectric Point (pI)', 'Net Charge (pH 7.0)', 'Aliphatic Index', 'Boman Index']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

def get_filter_options(_df):
    """Pre-compute all filter dropdown options once."""
    def extract_unique_values(series):
        return sorted(set(
            item.strip()
            for entry in series.dropna()
            for item in re.split(r'[;,]', str(entry))
            if item.strip()
        ))
 
    return {
        "family": sorted(_df['Family'].dropna().unique()),
        "organisms": extract_unique_values(_df['OS']),
        "tissue": extract_unique_values(_df['Tissue']),
        "ptm": extract_unique_values(_df['PTM']),
        "existence": extract_unique_values(_df['Existence']),
        "topic": extract_unique_values(_df['Topic']),
        "instrument": extract_unique_values(_df['Instrument']),
        "technique": extract_unique_values(_df['Technique']),
    }

filter_opts = get_filter_options(df)

# Create two columns with a 20px gap using Streamlit's built-in layout
col_filter, col_main = st.columns([1, 3], gap= "large")

# Custom container with manual gap
st.markdown('<div class="custom-col-container">', unsafe_allow_html=True)

# Filter column (1/4 width)
with col_filter:
    st.markdown('<div class="fill-height">', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Mass (Da))</div>', unsafe_allow_html=True)
    mono_mass_range = st.slider("", 200.0, 16000.0, (200.0, 16000.0), label_visibility="collapsed")

    st.markdown('<div class="section-title">Length (amino acids)</div>', unsafe_allow_html=True)
    length_range = st.slider("", 2, 150, (2, 150), label_visibility="collapsed")

    st.markdown('<div class="section-title">GRAVY Score</div>', unsafe_allow_html=True)
    gravy_range = st.slider("", -5.0, 5.0, (-5.0, 5.0), label_visibility="collapsed")

    st.markdown('<div class="section-title">% Hydrophobic Residue</div>', unsafe_allow_html=True)
    hydro_range = st.slider("", -1, 100, (-1, 100), label_visibility="collapsed")

    st.markdown('<div class="section-title">Instability Index</div>', unsafe_allow_html=True)
    instability_index_value = st.slider("", -100, 250, (-100, 250), label_visibility="collapsed")

    st.markdown('<div class="section-title">Isoelectric Point (pI)</div>', unsafe_allow_html=True)
    isoelectric_point_value = st.slider("", 0, 14, (0, 14), label_visibility="collapsed")

    st.markdown('<div class="section-title">Net Charge (pH 7.0)</div>', unsafe_allow_html=True)
    net_charge_value = st.slider("", -25, 10, (-25, 10), label_visibility="collapsed")

    st.markdown('<div class="section-title">Aliphatic Index</div>', unsafe_allow_html=True)
    aliphatic_index_value = st.slider("", 0, 390, (0, 390), label_visibility="collapsed")

    st.markdown('<div class="section-title">Boman Index</div>', unsafe_allow_html=True)
    boman_index_value = st.slider("", -0.45, 2.65, (-0.45, 2.65), label_visibility="collapsed")

    st.markdown('</div>', unsafe_allow_html=True)
        
# Main column (3/4 width)
with col_main:
    st.markdown("""
    <div class="fill-height" style="max-width: 100%; overflow-x: hidden;">
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom: 0px;" class="section-title">Peptide Sequence</div>
    <div style="margin-top: -30px;margin-bottom: -15px;">
    """, unsafe_allow_html=True)

    peptide_input = st.text_input(
        label=" ",
        placeholder="Separate by space, No PTMs included e.g., FDAFTTGFGHN ARPRNFLRF"
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # Family
    st.markdown('<div class="section-title" style="margin-top: -10px; margin-bottom: 8px;">Family</div>', unsafe_allow_html=True)
    family_selected = st.multiselect(label=" ", options=filter_opts["family"], key="fam", label_visibility="collapsed")

    # Organisms
    st.markdown('<div class="section-title" style="margin-top: 15px; margin-bottom: 8px">Organisms</div>', unsafe_allow_html=True)
    organisms_selected = st.multiselect(label=" ", options=filter_opts["organisms"], key="org", label_visibility="collapsed")

    # Tissue
    st.markdown('<div class="section-title" style="margin-top: 15px; margin-bottom: 8px">Tissue</div>', unsafe_allow_html=True)
    tissue_selected = st.multiselect(label=" ", options=filter_opts["tissue"], key="tissue", label_visibility="collapsed")

    # PTM
    st.markdown('<div class="section-title" style="margin-top: 15px; margin-bottom: 8px">Post-translational modifications (PTM)</div>', unsafe_allow_html=True)
    ptm_selected = st.multiselect(label=" ", options=filter_opts["ptm"], key="ptm", label_visibility="collapsed")

    # Existence
    st.markdown('<div class="section-title" style="margin-top: 15px; margin-bottom: 8px">Existence</div>', unsafe_allow_html=True)
    existence_selected = st.multiselect(label=" ", options=filter_opts["existence"], key="exist", label_visibility="collapsed")

     # --- NEW: Filters for Sheet 2 data ---
    st.markdown('<div class="section-title" style="margin-top: 15px; margin-bottom: 8px">Physiological Studies or Applications</div>', unsafe_allow_html=True)
    topic_selected = st.multiselect(label=" ", options=filter_opts["topic"], key="topic", label_visibility="collapsed")

    st.markdown('<div class="section-title" style="margin-top: 15px; margin-bottom: 8px">Instrument</div>', unsafe_allow_html=True)
    instrument_selected = st.multiselect(label=" ", options=filter_opts["instrument"], key="instrument", label_visibility="collapsed")
    
    st.markdown('<div class="section-title" style="margin-top: 15px; margin-bottom: 8px">Technique</div>', unsafe_allow_html=True)
    technique_selected = st.multiselect(label=" ", options=filter_opts["technique"], key="technique", label_visibility="collapsed")

    st.markdown('</div>', unsafe_allow_html=True)

# Close outer flex div
st.markdown('</div>', unsafe_allow_html=True)

def match_multivalue_column(selected_list, cell_value):
    """
    Check if any selected item is found in the split values of a cell (handles ; or , and trims spaces).
    """
    if pd.isna(cell_value):
        return False
    split_values = [entry.strip() for entry in re.split(r'[;,]', str(cell_value))]
    return any(sel.strip() in split_values for sel in selected_list)
    
# Filtering logic
df_filtered = df.copy()

# 1) Always apply peptide sequence search if provided
if peptide_input:
    peptides = peptide_input.split()
    # Create a regex pattern joining peptides with '|', meaning OR in regex
    pattern = '|'.join(peptides)
    df_filtered = df_filtered[df_filtered['Sequence'].str.contains(pattern, na=False)]

# 2) Apply right-side filters (multiselects) if any are selected
# These are "primary" filters - when used, they must be matched
right_filters_active = False

# Family filter
if family_selected:
    df_filtered = df_filtered[df_filtered['Family'].isin(family_selected)]
    right_filters_active = True

# Existence filter
if existence_selected:
    df_filtered = df_filtered[df_filtered['Existence'].isin(existence_selected)]
    right_filters_active = True
    
# --- MULTI-VALUE FILTERS ---
if tissue_selected:
    df_filtered = df_filtered[df_filtered['Tissue'].apply(
        lambda x: match_multivalue_column(tissue_selected, x)
    )]
    right_filters_active = True

if organisms_selected:
    df_filtered = df_filtered[df_filtered['OS'].apply(
        lambda x: match_multivalue_column(organisms_selected, x)
    )]
    right_filters_active = True

if ptm_selected:
    df_filtered = df_filtered[df_filtered['PTM'].apply(
        lambda x: match_multivalue_column(ptm_selected, x)
    )]
    right_filters_active = True

if topic_selected:
    df_filtered = df_filtered[df_filtered['Topic'].apply(
        lambda x: match_multivalue_column(topic_selected, x)
    )]
    right_filters_active = True

if instrument_selected:
    df_filtered = df_filtered[df_filtered['Instrument'].apply(
        lambda x: match_multivalue_column(instrument_selected, x)
    )]
    right_filters_active = True

if technique_selected:
    df_filtered = df_filtered[df_filtered['Technique'].apply(
        lambda x: match_multivalue_column(technique_selected, x)
    )]
    right_filters_active = True

# 3) Apply left-side sliders ONLY if:
#    - They're not at their default values, OR
#    - No right-side filters are active
default_ranges = {
    'Mass (Da)': (200.0, 16000.0),
    'Length': (2, 150),
    'GRAVY': (-5.0, 5.0),
    '% Hydrophobic Residue': (-1, 100),
    'Instability Index Value': (-100, 250),
    'Isoelectric Point (pI)': (0, 14),
    'Net Charge (pH 7.0)': (-25, 10),
    'Aliphatic Index': (0, 390),
    'Boman Index': (-0.45, 2.65),
}

# Only apply left slider filters if they differ from defaults OR no right filters are active
apply_slider_filters = (
    (mono_mass_range != default_ranges['Mass (Da)']) or
    (length_range != default_ranges['Length']) or
    (gravy_range != default_ranges['GRAVY']) or
    (hydro_range != default_ranges['% Hydrophobic Residue']) or
    (instability_index_value != default_ranges['Instability Index Value']) or
    (isoelectric_point_value != default_ranges['Isoelectric Point (pI)']) or
    (net_charge_value != default_ranges['Net Charge (pH 7.0)']) or
    (aliphatic_index_value != default_ranges['Aliphatic Index']) or
    (boman_index_value != default_ranges['Boman Index']) or
    (not right_filters_active)
)

if apply_slider_filters:
    df_filtered = df_filtered[
        df_filtered['Mass (Da)'].between(*mono_mass_range) &
        df_filtered['Length'].between(*length_range) &
        df_filtered['GRAVY'].between(*gravy_range) &
        df_filtered['% Hydrophobic Residue'].between(*hydro_range) &
        df_filtered['Instability Index Value'].between(*instability_index_value) &
        df_filtered['Isoelectric Point (pI)'].between(*isoelectric_point_value) &
        df_filtered['Net Charge (pH 7.0)'].between(*net_charge_value) &
        df_filtered['Aliphatic Index'].between(*aliphatic_index_value) &
        df_filtered['Boman Index'].between(*boman_index_value)
    ]
    
# --- Separator Line ---
st.markdown("""
<hr style='border: none; border-top: 2px solid #6a51a3; margin: 0px 30px;'>
""", unsafe_allow_html=True)

# Display results
st.markdown(
    '<h2 class="custom-title">'
    'SEARCH RESULTS'
    '</h2>',
    unsafe_allow_html=True
)

# 1) Inject opening container div
st.markdown(
    "<div class='results-container'>",
    unsafe_allow_html=True
)

if len(df_filtered) > 0:
    # Reserve a spot for buttons at the top
    button_container = st.container()
 
    # Hit count
    st.markdown(f"<div style='text-align: right; margin-bottom: 5px;'>Hit: {len(df_filtered)} peptides</div>", unsafe_allow_html=True)
    
    # Check/Uncheck All
    check_all = st.checkbox("Check/Uncheck All")
 
    # Reserve a spot for View Details panel (between checkbox and cards)
    details_container = st.container()
 
    # 4) Peptide cards in three columns
    selected_indices = []
    cols = st.columns(3)
 
    for i, (idx, row) in enumerate(df_filtered.iterrows()):
        with cols[i % 3]:
            checked = st.checkbox("", key=f"check_{idx}", value=check_all)
            if checked:
                selected_indices.append(idx)
 
            # Clean organism field to only show unique values
            org_raw = str(row['OS']) if pd.notna(row['OS']) else ""
            org_list = [item.strip() for item in org_raw.split(';') if item.strip()]
            org_unique = "; ".join(sorted(set(org_list), key=org_list.index))
 
            st.markdown(f"""
                <div style='max-width:100%; overflow-x:auto; padding-right:4px;'>
                    <div style='border:1px solid #6A0DAD; padding:10px; margin-bottom:20px; border-radius:10px;'>
                        <div style="
                            font-weight:bold;
                            background-color:#6a51a3;
                            color:white;
                            padding:10px;
                            border-radius: 6px;
                            max-width: 100%;
                            overflow-x: auto;
                            white-space: nowrap;
                            font-family: monospace;
                            font-size: 13px;
                        ">
                            {row['Active Sequence']}
                        </div>
                        <div style='padding:5px; font-size:14px; overflow-wrap:break-word;'>
                            Family: {row['Family']}<br>
                            Organism: {org_unique}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
 
    # Now fill the button container that we reserved at the top
    selected_rows = df_filtered.loc[selected_indices] if selected_indices else pd.DataFrame()
 
    with button_container:
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
 
        # View Details
        with col1:
            left_space, right_button = st.columns([1,4])
            with right_button:
                if "view_details" not in st.session_state:
                    st.session_state.view_details = False
 
                if st.button("View Details", type="primary"):
                    st.session_state.view_details = True
 
        # Download Excel
        with col2:
            with st.container():
                if selected_rows.empty:
                    st.button("Download Search Results", type="primary", disabled=True)
                else:
                    excel_buf = io.BytesIO()
                    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                        selected_rows.to_excel(writer, index=False, sheet_name="Selected")
                    excel_buf.seek(0)
                    st.download_button(
                        "Download Search Results",
                        data=excel_buf,
                        file_name="cNPDB_Search_Results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        key="download_excel"
                    )
 
        # Download FASTA File
        with col3:
            with st.container():
                if selected_rows.empty:
                    st.button("Download FASTA File", type="primary", disabled=True)
                else:
                    fasta_str = "\n".join(
                    f">{str(row['ID']).lstrip('>')}\n{str(row['Sequence'])}"
                    for _, row in selected_rows.iterrows()
                    )
                    st.download_button(
                        "Download FASTA File",
                        data=fasta_str,
                        file_name="cNPDB_Search_Result.fasta",
                        mime="text/plain",
                        type="primary",
                        key="download_fasta"
                    )
 
        # Download ZIP (CIF + MSI)
        with col4:
            with st.container():
                if selected_rows.empty:
                    st.button("Download 3D Structures + MSI", type="primary", disabled=True)
                else:
                    zip_buf = io.BytesIO()
                    with zipfile.ZipFile(zip_buf, "w") as zipf:
                        for _, row in selected_rows.iterrows():
                            cnp_id = int(row["cNPDB ID"])
 
                            # Determine AlphaFold folder
                            if cnp_id <= 1000:
                                alphafold_folder = "Assets/3D Structure AlphaFold 1_1000"
                            else:
                                alphafold_folder = "Assets/3D Structure AlphaFold 1001_2000"
 
                            cif_path = os.path.join(alphafold_folder, f"3D cNP {cnp_id}.cif")
                            if os.path.exists(cif_path):
                                zipf.write(cif_path, arcname=f"AlphaFold_3D_Structures/{os.path.basename(cif_path)}")
 
                            # Determine ESMFold folder
                            if cnp_id <= 1000:
                                esmfold_folder = "Assets/3D Structure ESMFold 1_1000"
                            else:
                                esmfold_folder = "Assets/3D Structure ESMFold 1001_2000"
 
                            pdb_path = os.path.join(esmfold_folder, f"3D Meta cNP{cnp_id}.pdb")
                            if os.path.exists(pdb_path):
                                zipf.write(pdb_path, arcname=f"ESMfold_3D_Structures/{os.path.basename(pdb_path)}")
 
 
                            # Add MSI images
                            for tissue_col, asset_folder in [
                                ("MSI Tissue 1", "Assets/MSImaging"),
                                ("MSI Tissue 2", "Assets/MSImaging"),
                                ("MSI Tissue 3", "Assets/MSImaging"),
                            ]:
                                suffix = " " + tissue_col.split()[-1]
                                msi_path = f"{asset_folder}/MSI cNP{cnp_id}{suffix}.jpeg"
                                if os.path.exists(msi_path):
                                    zipf.write(msi_path, arcname=f"MSI_Images/{os.path.basename(msi_path)}")
 
                    zip_buf.seek(0)
                    st.download_button(
                        "Download 3D Structures + MSI",
                        data=zip_buf,
                        file_name="cNPDB_3D_Structures_MSI.zip",
                        mime="application/zip",
                        type="primary",
                        key="download_zip"
                    )
 
        # Warning appears inside button_container (above cards)
        if st.session_state.view_details and selected_rows.empty:
            st.warning("⚠️ Please select at least one peptide to view details.")
 
    # View Details panel — fills the reserved spot above the cards
    if st.session_state.view_details and not selected_rows.empty:
        with details_container:
            for _, row in selected_rows.iterrows():
                display_peptide_details(row)
                st.markdown("<hr style='border: 1px solid #6a51a3; margin: 40px 0;'>", unsafe_allow_html=True)
 
else:
    st.warning("❌ No peptides match your search criteria. Please refine your parameters.")
 
# 5) Close container div
st.markdown(
    "</div>",
    unsafe_allow_html=True
)
 
# Footer
st.markdown("""
<div style="text-align: center; font-size:14px; color:#2a2541;">
  <em>Last update: Jul 2026</em>
</div>
""", unsafe_allow_html=True)
