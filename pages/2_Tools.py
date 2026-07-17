import streamlit as st
from sidebar import render_sidebar
from Bio.SeqUtils.ProtParam import ProteinAnalysis
import pandas as pd
from Bio import pairwise2
from io import StringIO
from Bio.Align import substitution_matrices
import re

# Physicochemical-property and sequence logic live in shared, unit-tested
# modules so the app, database, and QC scripts never drift apart.
from utils.peptide_properties import (
    calculate_properties,
    BOMAN_SCALE as boman_scale,
    HYDROPHOBIC_RESIDUES as hydrophobic_residues,
)
from utils.sequence_utils import clean_sequence, calculate_percent_identity

# from utils.session_tracker import track_session
# track_session()


st.set_page_config(
    page_title="Tools",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_sidebar()
st.markdown(
    """
    <style>
      
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("""
    <style>
    .stDownloadButton>button {
        background-color: #54278f !important;
        color: white !important;
        border: none;
        border-radius: 0.5rem;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: background-color 0.2s ease;
    },
    .stDownloadButton>button:hover {
        background-color: #3f007d !important;
    },
    /* Prevent horizontal scroll */
    body, .main, .block-container {
    overflow-x: hidden !important;
    },
    /* Limit max width of the entire interface */
    .main-search-container {
    max-width: 100vw;
    overflow-x: hidden;
    }      
</style>
""", unsafe_allow_html=True)

# Page layout
st.markdown("""
<style>
 /* 1) Centered title with10px top margin */
  h2.custom-title {
    text-align: center !important;
    margin-top: 0px !important;
    color: #29004c;
  }
</style>
""", unsafe_allow_html=True)

# --- Peptide property calculator ---
st.markdown(
    '<h2 class="custom-title">'
    'PEPTIDE PROPERTY CALCULATOR'
    '</h2>',
    unsafe_allow_html=True
)

sequence_input = st.text_area("Enter your peptide sequence:", height=68)

# Centered Calculate Button
col_calc1, col_calc2, col_calc3 = st.columns([1.7, 1, 1])
with col_calc2:
    calculate_clicked = st.button("Calculate", type="primary")

if calculate_clicked:
    if not sequence_input.strip():
        st.error("Please enter a peptide sequence")
    else:
        try:
            props = calculate_properties(sequence_input)
            st.markdown("### Peptide Property Results")
            for key, value in props.items():
                st.write(f"**{key}**: {value}")
        except Exception as e:
            st.error(f"Error: {e}")

# --- Separator Line ---
st.markdown("""
<hr style='border: none; border-top: 2px solid #6a51a3; margin-top: 10px; margin-bottom: 0px; margin-left: 30px; margin-right: 30px;'>
""", unsafe_allow_html=True)


# --- peptide allignment Search ---
st.markdown(
    '<h2 class="custom-title">'
    'PEPTIDE SEQUENCE ALIGNMENT'
    '</h2>',
    unsafe_allow_html=True
)

st.markdown("""
<div style='font-size:15px; padding:10px 10px;'>
Peptide Alignment allows users to align two peptide sequences of interest or against cNPDB. Default settings are suitable for most neuropeptide alignments, but users can modify the alignment parameters for custom analysis. For more guidance, please refer to the <i>Glossary</i> and <i>Tutorials</i> pages.
</div>
""", unsafe_allow_html=True)

# Load peptide sequence database
@st.cache_data
def load_data():
    return pd.read_parquet("Assets/20260717_cNPDB.parquet")

df = load_data()

# Initialize default values in session_state if not set
if "match_score" not in st.session_state:
    st.session_state.match_score = 2
if "mismatch_score" not in st.session_state:
    st.session_state.mismatch_score = -1
if "gap_open" not in st.session_state:
    st.session_state.gap_open = -0.5
if "gap_extend" not in st.session_state:
    st.session_state.gap_extend = -0.1
if "alignment_type" not in st.session_state:
    st.session_state.alignment_type = "global"
if "query_seq" not in st.session_state:
    st.session_state.query_seq = ""
if "target_seq" not in st.session_state:
    st.session_state.target_seq = ""
if "use_database" not in st.session_state:
    st.session_state.use_database = False

# Reset button (centered above inputs)
col_reset_left, col_reset_mid, col_reset_right = st.columns([1.8, 1, 1])
with col_reset_mid:
    if st.button("Reset", type="primary"):
        # Reset all session state keys to default values
        st.session_state.match_score = 2
        st.session_state.mismatch_score = -1
        st.session_state.gap_open = -0.5
        st.session_state.gap_extend = -0.1
        st.session_state.alignment_type = "global"
        st.session_state.query_seq = ""
        st.session_state.target_seq = ""
        st.session_state.use_database = False


# Utility functions (clean_sequence and calculate_percent_identity are imported
# from utils.sequence_utils above)
def custom_format_alignment(aln):
    seqA = aln.seqA
    seqB = aln.seqB
    midline = "".join("|" if a == b else " " for a, b in zip(seqA, seqB))
    identity = calculate_percent_identity(seqA, seqB)
    return f"{seqA}\n{midline}\n{seqB}", identity

def generate_alignment_text(query_seq, alignment_type, match_score, mismatch_score, gap_open, gap_extend, top_hits, df):
    report = StringIO()
    summary_data = []

    df_summary = pd.DataFrame(columns=["No", "Family", "Sequence", "Score", "Percent Identity"])

    for i, (score, db_seq, aln) in enumerate(top_hits):
        if aln:
            formatted, identity = custom_format_alignment(aln)
        else:
            formatted, identity = "\u26a0\ufe0f No valid alignment.", 0

        match_row = df[df["Sequence"] == db_seq].iloc[0] if not df[df["Sequence"] == db_seq].empty else None
        family = match_row.get('Family', 'N/A') if match_row is not None else 'N/A'
        organism = match_row.get('OS', 'N/A') if match_row is not None else 'N/A'
        tissue = match_row.get('Tissue', 'N/A') if match_row is not None else 'N/A'
        active_seq = match_row.get('Active Sequence', 'N/A') if match_row is not None else 'N/A'
        
        summary_data.append((i + 1, family, db_seq, score, identity))

    df_summary = pd.DataFrame(summary_data, columns=["No", "Family", "Sequence", "Score", "Percent Identity"])
    df_summary = df_summary.sort_values(by=["Score", "Percent Identity"], ascending=[False, False])
    df_summary.set_index("No", inplace=True)

    # Report content starts
    report.write("Peptide Sequence Alignment Report\n")
    report.write("="*40 + "\n")
    report.write(f"Query Sequence: {query_seq}\n")
    report.write(f"Alignment Type: {alignment_type}\n")
    report.write(f"Match Score: {match_score}, Mismatch Penalty: {mismatch_score}\n")
    report.write(f"Gap Open: {gap_open}, Gap Extend: {gap_extend}\n\n")

    # Summary Table FIRST
    report.write("Summary Table\n")
    report.write("="*40 + "\n")
    report.write(df_summary.to_string(index=False))
    report.write("\n\nAlignment Details\n")
    report.write("="*40 + "\n")

    for i, (score, db_seq, aln) in enumerate(top_hits):
        report.write(f"Hit #{i+1} - Score: {score:.2f}, Percent Identity: {identity:.2f}%\n")
        report.write("-"*30 + "\n")
        if aln:
            formatted, identity = custom_format_alignment(aln)
            report.write(formatted + "\n")
        else:
            report.write("\u26a0\ufe0f No valid alignment.\n")

        match_row = df[df["Sequence"] == db_seq].iloc[0] if not df[df["Sequence"] == db_seq].empty else None
        if match_row is not None:
            report.write(f"Family: {match_row.get('Family', 'N/A')}\n")
            report.write(f"Organism (OS): {match_row.get('OS', 'N/A')}\n")
            report.write(f"Tissue: {match_row.get('Tissue', 'N/A')}\n")
            report.write(f"Active Sequence: {match_row.get('Active Sequence', 'N/A')}\n")
        
        report.write("\n")

    return report.getvalue(), df_summary

# User input
query_seq = st.text_area("Enter your peptide sequence (Only one sequence at a time):", height=68, key="query_seq")
target_seq = st.text_area("Enter second sequence for alignment (optional):", height=68, key="target_seq")

query_seq = clean_sequence(query_seq)
target_seq = clean_sequence(target_seq)

if not st.session_state.target_seq:
    use_database = st.checkbox(
        "Align against the cNPDB database",
        key="use_database",
        value=st.session_state.use_database
    )
else:
    use_database = None

# Alignment parameters
st.markdown("### Alignment Settings")
col_param = st.columns(5)
with col_param[0]:
    alignment_type = st.selectbox("Type", ["global", "local"], key="alignment_type")
with col_param[1]:
    match_score = st.number_input("Match", key="match_score")
with col_param[2]:
    mismatch_score = st.number_input("Mismatch", key="mismatch_score")
with col_param[3]:
    gap_open = st.number_input("Gap Open", key="gap_open")
with col_param[4]:
    gap_extend = st.number_input("Gap Extend", key="gap_extend")

# Run Alignment Button
button_disabled = not st.session_state.query_seq or (not st.session_state.use_database and not st.session_state.target_seq)
col1, col2, col3 = st.columns([1.7, 1, 1])
with col2:
    run_clicked = st.button("Run Alignment", type="primary")

if run_clicked:
    if not st.session_state.query_seq.strip():
        st.error("\u274c Please input your peptide sequence.")
    elif not st.session_state.use_database and not st.session_state.target_seq.strip():
        st.error("\u274c Please input the second sequence or choose to align against the cNPDB database.")
    else:
        if not use_database:
            try:
                alignments = (
                    pairwise2.align.globalms(query_seq, target_seq, match_score, mismatch_score, gap_open, gap_extend)
                    if alignment_type == "global" else
                    pairwise2.align.localms(query_seq, target_seq, match_score, mismatch_score, gap_open, gap_extend)
                )
                formatted, identity = custom_format_alignment(alignments[0])
                st.success("Top alignment result:")
                st.code(f"{formatted}\n\nPercent Identity: {identity:.2f}%")
            except Exception as e:
                st.error(f"Alignment failed: {e}")
        else:
            results = []
            for i, db_seq in enumerate(df["Sequence"]):
                try:
                    aln = (
                        pairwise2.align.globalms(query_seq, db_seq, match_score, mismatch_score, gap_open, gap_extend, one_alignment_only=True)
                        if alignment_type == "global" else
                        pairwise2.align.localms(query_seq, db_seq, match_score, mismatch_score, gap_open, gap_extend, one_alignment_only=True)
                    )
                    score = aln[0].score if aln else 0
                    results.append((score, db_seq, aln[0] if aln else None))
                except Exception:
                    continue

            top_hits = sorted(results, key=lambda x: -x[0])[:10]
            st.success("Top 10 alignment hits from cNPDB database:")

            alignment_txt, df_summary = generate_alignment_text(
                query_seq, alignment_type, match_score, mismatch_score, gap_open, gap_extend, top_hits, df
            )

            col_dl1, col_dl2, col_dl3 = st.columns([1.3, 1, 1])
            with col_dl2:
                st.download_button(
                    label="Download Alignment Results",
                    data=alignment_txt,
                    file_name="cNPDB_alignment_results.txt",
                    mime="text/plain"
                )

            st.markdown("### Top Hits Sorted by Score & Percent Identity")
            st.dataframe(
                df_summary,
                use_container_width=True,
                column_config={
                    "Family": st.column_config.Column(width="small"),
                    "Sequence": st.column_config.Column(width="large"),
                    "Score": st.column_config.Column(width="small"),
                    "Percent Identity": st.column_config.Column(width="small"),
                }
            )

            for i, (score, db_seq, aln) in enumerate(top_hits):
                match_row = df[df["Sequence"] == db_seq].iloc[0] if not df[df["Sequence"] == db_seq].empty else None
                formatted, identity = custom_format_alignment(aln) if aln else ("No valid alignment.", 0)

                st.markdown(f"""
                    <div style='padding:10px 0;'>
                        <span style='font-size:16px; color:#54278f; font-weight:bold;'>Hit #{i+1}</span><br>
                        <span style='font-size:16px;'>Score: <span style='color:#238b45; font-weight:bold;'>{score:.2f}</span></span><br>
                        <span style='font-size:16px;'>Identity: <span style='color:#e6550d; font-weight:bold;'>{identity:.2f}%</span></span>
                    </div>
                """, unsafe_allow_html=True)

                st.code(formatted)

                if match_row is not None:
                    st.markdown(f"""
                    <div style='font-size:15px; margin-bottom:20px;'>
                        <strong>Family:</strong> {match_row.get("Family", "N/A")}<br>
                        <strong>Organisms:</strong> {match_row.get("OS", "N/A")}<br>
                        <strong>Tissue:</strong> {match_row.get("Tissue", "N/A")}<br>
                        <strong>Active Sequence:</strong> {match_row.get("Active Sequence", "N/A")}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("No additional info found for this hit.")

# --- Sequence alignment calculator ---
# st.markdown(
    # '<h2 class="custom-title">'
    # 'PEPTIDE SEQUENCE ALIGNMENT'
    # '</h2>',
    # unsafe_allow_html=True
# )

# st.markdown("""
# <div style='font-size:15px; padding:10px 10px;'>
# Peptide Alignment allows users to align two peptide sequences of interest. Default settings are suitable for most neuropeptide alignments, but users can modify the alignment parameters for custom analysis. For more guidance, please refer to the <i>Glossary</i> and <i>Tutorials</i> pages.
# </div>
# """, unsafe_allow_html=True)

# def clean_sequence(seq):
    # lines = seq.strip().splitlines()
    # clean_lines = [line.strip() for line in lines if not line.startswith(">")]
    # return ''.join(clean_lines).upper()

# def custom_format_alignment(aln):
    # seqA = aln.seqA
    # seqB = aln.seqB
    # midline = ""

    # for a, b in zip(seqA, seqB):
        # if a == b:
            # midline += "|"
        # else:
            # midline += " "

    # return f"{seqA}\n{midline}\n{seqB}"
    
# def compute_percent_identity(aln):
    # matches = sum(1 for a, b in zip(aln.seqA, aln.seqB) if a == b)
    # length = len(aln.seqA)  # Includes gaps
    # percent_identity = (matches / length) * 100 if length > 0 else 0
    # return matches, length, percent_identity

# def generate_alignment_text(query_seq, target_seq, alignment_type, match_score, mismatch_score, gap_open, gap_extend, alignment):
    # matches, length, percent_identity = compute_percent_identity(alignment)
    # report = StringIO()
    # report.write("Pairwise Peptide Alignment Report\n")
    # report.write("="*40 + "\n")
    # report.write(f"Query Sequence: {query_seq}\n")
    # report.write(f"Target Sequence: {target_seq}\n")
    # report.write(f"Alignment Type: {alignment_type}\n")
    # report.write(f"Match Score: {match_score}, Mismatch Penalty: {mismatch_score}\n")
    # report.write(f"Gap Open: {gap_open}, Gap Extend: {gap_extend}\n")
    # report.write(f"\nAlignment Score: {alignment.score:.2f}\n\n")
    # report.write(f"Alignment Length: {length}\n")
    # report.write(f"Identical Matches: {matches}\n")
    # report.write(f"Percent Identity: {percent_identity:.2f}%\n\n")
    # report.write(custom_format_alignment(alignment) + "\n")
    # return report.getvalue()

# --- Default values for resetting ---
# default_values = {
    # "query_seq": "",
    # "target_seq": "",
    # "match_score": 2,
    # "mismatch_score": -1,
    # "gap_open": -0.5,
    # "gap_extend": -0.1,
    # "alignment_type": "global"
# }

# Initialize session_state variables if not present
# for key, val in default_values.items():
    # if key not in st.session_state:
        # st.session_state[key] = val

# Handle Reset button first — this must happen before widgets are created!
# col1, col2, col3 = st.columns([1.8, 1, 1])
# with col2:
    # reset = st.button("Reset", key="reset_alignment", type="primary")
# if reset:
    # for key, val in default_values.items():
        # st.session_state[key] = val
    # st.rerun()

# Text areas (just use keys, no `value=`)
# query_seq = st.text_area("Enter first peptide sequence:", key="query_seq", height=68)
# target_seq = st.text_area("Enter second sequence for alignment:", key="target_seq", height=68)

# Alignment parameters in compact column layout
# st.markdown("### Alignment Settings")
# col_param = st.columns(5)
# with col_param[0]:
    # alignment_type = st.selectbox("Type", ["global", "local"], index=0 if st.session_state.alignment_type == "global" else 1, key="alignment_type")
# with col_param[1]:
    # match_score  = st.number_input("Match", key="match_score")
# with col_param[2]:
    # mismatch_score = st.number_input("Mismatch", key="mismatch_score")
# with col_param[3]:
    # gap_open = st.number_input("Gap Open", key="gap_open")
# with col_param[4]:
    # gap_extend = st.number_input("Gap Extend", key="gap_extend")

# Run Alignment Button
# col1, col2, col3 = st.columns([1.5, 1, 1])
# with col2:
    # run_clicked = st.button("Run Alignment", type="primary", key="run_button")

# if run_clicked:
    # cleaned_query = clean_sequence(st.session_state.query_seq)
    # cleaned_target = clean_sequence(st.session_state.target_seq)

    # if not cleaned_query or not cleaned_target:
        # st.error("❌ Please input both peptide sequences.")
    # else:
        # try:
            # align_func = pairwise2.align.globalms if st.session_state.alignment_type == "global" else pairwise2.align.localms
            # alignments = align_func(
                # cleaned_query,
                # cleaned_target,
                # st.session_state.match_score,
                # st.session_state.mismatch_score,
                # st.session_state.gap_open,
                # st.session_state.gap_extend
            # )
            # if alignments:
                # top_alignment = alignments[0]
                # matches, aln_length, percent_id = compute_percent_identity(top_alignment)

                # st.success("Alignment result:")
                # st.markdown(f"""
                # - **Alignment Score:** {top_alignment.score:.2f}  
                # - **Alignment Length:** {aln_length}  
                # - **Identical Matches:** {matches}  
                # - **Percent Identity:** {percent_id:.2f}%
                # """)
                # st.code(custom_format_alignment(top_alignment))

                # alignment_txt = generate_alignment_text(
                    # cleaned_query,
                    # cleaned_target,
                    # st.session_state.alignment_type,
                    # st.session_state.match_score,
                    # st.session_state.mismatch_score,
                    # st.session_state.gap_open,
                    # st.session_state.gap_extend,
                    # top_alignment
                # )

                # col_dl1, col_dl2, col_dl3 = st.columns([1.3, 1, 1])
                # with col_dl2:
                    # st.download_button(
                        # label="Download Alignment Result",
                        # data=alignment_txt,
                        # file_name="cNPDB_pairwise_alignment.txt",
                        # mime="text/plain"
                    # )
            # else:
                # st.warning("No valid alignment found.")
        # except Exception as e:
            # st.error(f"❌ Alignment failed: {e}")

# --- Separator Line ---
# st.markdown("""
# <hr style='border: none; border-top: 3px solid #6a51a3;  margin-top: 10px; margin-bottom: 0px; margin-left: 30px; margin-right: 30px;'>
# """, unsafe_allow_html=True)

# --- BLAST Search ---
# st.markdown(
    # '<h2 class="custom-title">'
    # 'BLAST SEARCH'
    # '</h2>',
    # unsafe_allow_html=True
# )

# st.markdown("""
# <div style='font-size:15px; padding:10px 10px;'>
# BLAST Search allows users to compare their peptide sequence against the cNPDB database and identify similar neuropeptides. Default parameters are optimized for typical neuropeptide BLAST searches, but users can customize settings to suit their needs. See <i>Glossary</i> and <i>Tutorials</i> pages for more details.
# </div>
# """, unsafe_allow_html=True)

# --- BLAST SESSION STATE DEFAULTS ---
# blast_defaults = {
    # "query_input": "",
    # "e_value_thresh": 10.0,
    # "matrix_select": "BLOSUM80",
    # "gap_open_blast": -10.0,
    # "gap_extend_blast": -0.5,
    # "word_size": 3,
    # "top_n": 10,
    # "seg_filter": True,
    # "comp_bias": True
# }

# for key, val in blast_defaults.items():
    # if key not in st.session_state:
        # st.session_state[key] = val

# Handle Reset button first — this must happen before widgets are created!
# col1, col2, col3 = st.columns([1.8, 1, 1])
# with col2:
    # reset_blast = st.button("Reset", key="reset_blast", type="primary")
# if reset_blast:
    # for key, val in blast_defaults.items():
        # st.session_state[key] = val
    # st.rerun()

# @st.cache_data
# def load_db():
    # return pd.read_parquet("Assets/20260418_cNPDB.parquet", sheet_name="Sheet 1")

# df = load_db()

# --- Input ---
# query_input = st.text_area("Enter your peptide sequence (Only one sequence at a time):", key="query_input", height=69)

# def parse_sequence(text):
    # lines = text.strip().splitlines()
    # clean = [l.strip() for l in lines if not l.startswith(">")]
    # sequence = ''.join(clean).upper()
    # return sequence

# query_seq = parse_sequence(st.session_state.query_input)

# --- Settings ---
# st.sidebar.header("BLAST Settings")

# st.markdown("### BLAST Settings")
# col_param = st.columns(5)
# with col_param[0]:
    # e_value_thresh = st.number_input("E-value Threshold", key="e_value_thresh", step=0.1)
# with col_param[1]:
    # matrix_options = ["BLOSUM62", "BLOSUM80", "BLOSUM45", "PAM30", "PAM70"]
    # st.selectbox("Matrix", matrix_options, key="matrix_select")
# with col_param[2]:
    # gap_open = st.number_input("Gap Open", key="gap_open_blast", step=0.5)
# with col_param[3]:
    # gap_extend = st.number_input("Gap Extend", key="gap_extend_blast", step=0.1)
# with col_param[4]:
    # word_size = st.slider("Word Size", 2, 4, key="word_size")

# col_opt = st.columns(2)
# with col_opt[0]:
    # top_n = st.selectbox("Number of Top Hits", [5, 10, 20], key="top_n")   
# with col_opt[1]:
    # seg_filter = st.checkbox("SEG Filtering", key="seg_filter")
    # comp_bias = st.checkbox("Composition-based Stats", key="comp_bias")

# Load and convert substitution matrix to pairwise2-compatible format
# mat = substitution_matrices.load(st.session_state.matrix_select)
# scoring_matrix = { (a, b): mat[a][b] for a in mat.alphabet for b in mat.alphabet }

# Format alignment manually
# def format_alignment(aln):
    # seqA, seqB = aln.seqA, aln.seqB
    # midline = ''.join(['|' if a == b else ' ' for a, b in zip(seqA, seqB)])
    # return f"{seqA}\n{midline}\n{seqB}"

# --- Generate report text ---
# def generate_blast_text(query_seq, e_value_thresh, matrix_choice, gap_open, gap_extend, word_size, results, df):
    # report = StringIO()
    # report.write("cNPDB BLAST Report\n")
    # report.write("="*40 + "\n")
    # report.write(f"Query Sequence:\n{query_seq}\n\n")
    # report.write("Settings:\n")
    # report.write(f"E-value Threshold: {e_value_thresh}\n")
    # report.write(f"Matrix: {matrix_choice}\n")
    # report.write(f"Gap Open Penalty: {gap_open}\n")
    # report.write(f"Gap Extend Penalty: {gap_extend}\n")
    # report.write(f"Word Size: {word_size}\n\n")
    
    # for i, (score, e_val, db_seq, aln) in enumerate(results):
        # report.write(f"Hit #{i+1} - Score: {score:.2f} | E-value: {e_val:.2e}\n")
        # if aln:
            # seqA, seqB = aln.seqA, aln.seqB
            # midline = ''.join(['|' if a == b else ' ' for a, b in zip(seqA, seqB)])
            # identity = sum(a == b for a, b in zip(seqA, seqB))
            # aln_len = len(seqA)
            # identity_pct = (identity / aln_len) * 100 if aln_len > 0 else 0
            # report.write(f"{seqA}\n{midline}\n{seqB}\n")
            # report.write(f"Identity: {identity_pct:.1f}% | Alignment Length: {aln_len}\n")
        # else:
            # report.write("No valid alignment available.\n")

        # row = df[df["Sequence"] == db_seq]
        # if not row.empty:
            # row = row.iloc[0]
            # report.write(f"Family: {row.get('Family', 'N/A')}\n")
            # report.write(f"Organism: {row.get('OS', 'N/A')}\n")
            # report.write(f"Tissue: {row.get('Tissue', 'N/A')}\n")
            # report.write(f"Active Sequence: {row.get('Active Sequence', 'N/A')}\n")
        # report.write("\n")

   # return report.getvalue()

# col1, col2, col3 = st.columns([1.6, 1, 1])
# with col2:
    # run = st.button("Run BLAST", type="primary")

# Run BLAST
# if run:
    # seq_for_search = query_seq
    # if st.session_state.seg_filter:
        # seq_for_search = re.sub(r'[^A-Z]', '', seq_for_search)
        # seq_for_search = re.sub(r'(.)\1{3,}', '', seq_for_search)

    # results = []
    # for i, db_seq in enumerate(df["Sequence"]):
        # db_seq_clean = db_seq
        # if st.session_state.seg_filter:
            # db_seq_clean = re.sub(r'[^A-Z]', '', db_seq_clean)
            # db_seq_clean = re.sub(r'(.)\1{3,}', '', db_seq_clean)

        # if len(seq_for_search) < st.session_state.word_size or len(db_seq_clean) < st.session_state.word_size:
            # continue

        # try:
            # aln = pairwise2.align.localds(seq_for_search, db_seq_clean, scoring_matrix, st.session_state.gap_open, st.session_state.gap_extend, one_alignment_only=True)
            # score = aln[0].score if aln else 0
            # e_val = 1e-5 * (100 - score / len(seq_for_search)) * (i + 1)
            # if st.session_state.comp_bias:
                # bias_penalty = abs(len(seq_for_search) - len(db_seq_clean)) * 0.01
                # e_val += bias_penalty

            # if e_val <= st.session_state.e_value_thresh:
                # results.append((score, e_val, db_seq, aln[0] if aln else None))
        # except Exception:
            # continue

    # results = sorted(results, key=lambda x: -x[0])[:st.session_state.top_n]

    # if not results:
        # st.warning(f"No hits found with E-value ≤ {st.session_state.e_value_thresh}.")
    # else:
        # st.success(f"{len(results)} hit(s) found with E-value ≤ {st.session_state.e_value_thresh}")

        # blast_txt = generate_blast_text(query_seq, st.session_state.e_value_thresh,
                                        # st.session_state.matrix_select, st.session_state.gap_open,
                                        # st.session_state.gap_extend, st.session_state.word_size, results, df)

        # col_dl1, col_dl2, col_dl3 = st.columns([1.35, 1, 1])
        # with col_dl2:
            # st.download_button(
                # label="Download BLAST Results",
                # data=blast_txt,
                # file_name="cNPDB_BLAST_results.txt",
                # mime="text/plain"
            # )

        # for i, (score, e_val, db_seq, aln) in enumerate(results):
            # st.subheader(f"Hit #{i+1}")
            # if aln:
                # identical = sum(a == b for a, b in zip(aln.seqA, aln.seqB))
                # aln_length = len(aln.seqA)
                # identity_pct = (identical / aln_length) * 100 if aln_length > 0 else 0
                # st.text(f"Score: {score:.2f} | E-value: {e_val:.2e} | Identity: {identity_pct:.1f}% | Length: {aln_length}")
                # st.code(format_alignment(aln))
            # else:
                # st.text(f"Score: {score:.2f} | E-value: {e_val:.2e}")
                # st.warning("No alignment available")

            # row = df[df["Sequence"] == db_seq]
            # if not row.empty:
                # row = row.iloc[0]
                # st.markdown(f"""
                    # **Family**: {row.get('Family', 'N/A')}  
                    # **Organism**: {row.get('OS', 'N/A')}  
                    # **Tissue**: {row.get('Tissue', 'N/A')}  
                    # **Active Sequence**: {row.get('Active Sequence', 'N/A')}
                # """)

st.markdown("""
<div style="text-align: center; font-size:14px; color:#2a2541;">
  <em>Last update: Jul 2026</em>
</div>
""", unsafe_allow_html=True)
