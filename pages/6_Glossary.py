import streamlit as st
from sidebar import render_sidebar

# from utils.session_tracker import track_session
# track_session()

st.set_page_config(
    page_title="Glossary",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_sidebar()

# Inject custom CSS for the glossary layout
st.markdown("""
<style>
/* Section heading */
.section-heading {
  color: #29004c;
  font-size: 30px;
  font-weight: bold;
  margin-top: 2rem;
  margin-bottom: 0.25rem;
  position: relative;
  padding-bottom: 0.25rem;
  text-transform:uppercase;
}

/* Two‐column item: term on left, definition on right */
.glossary-item {
  display: grid;
  grid-template-columns: 20% 80%;
  margin-bottom: 10px;
  align-items: stretch;
}

/* Term cell */
.glossary-term {
  background-color: #7e7ba0;
  color: white;
  padding: 10px 20px;
  border-radius: 10px 0 0 10px;
  font-weight: bold;
  text-align: left;
}

/* Definition cell */
.glossary-def {
  background-color: white;
  color: #333;
  padding: 10px 10px;
  border: 3px solid #7e7ba0;
  border-radius: 0 10px 10px 0;
  display: flex;
  align-items: center;
}

/* Ensure definitions wrap and justify nicely */
.glossary-def p {
  margin: 0;
  text-align: justify;
}
</style>
""", unsafe_allow_html=True)

# Define your glossary content
tissues = [
    ("Br",     "Brain - Modulates and initiates signalling communications and responses to external stimuli"),
    ("CG",     "Cardiac Ganglion - Embeds inside the heart muscle, regulates cardiac muscle contractions and heartbeat"),
    ("CNS",    "Central Nervous System - Controls and coordinates sensory input, motor functions, and behavior"),
    ("CoG",    "Commissural Ganglion - Coordinates signals between the brain and the stomatogastric ganglion for gut motility"),
    ("ES",     "Eyestalk Ganglia - Acts as a neurosecretory center, contains neurosecretory cells (also called X-organ) that synthesize neuropeptides and hormones"),
    ("OG",     "Oesophageal Ganglion - Integrates neural signals between the brain and lower ganglia"),
    ("OVR",    "Ovary - Regulates reproductive processes such as vitellogenesis and oocyte maturation"),
    ("PO",     "Pericardial Organ - Locates at two sides of the heart, secretes neuropeptides into the hemolymph to reach distant organs, affecting cardiac and downstream physiological processes"),
    ("SG",     "Sinus Gland - Locates in the eyestalks, stores and releases neurohormones that regulate molting, reproduction, and metabolism"),
    ("STG",    "Stomatogastric Ganglion - Locates in the foregut region, controls rhythmic muscle contractions for stomach and gut function"),
    ("TG",     "Thoracic Ganglion - Situates in the thorax, manages motor control of walking legs and other appendages"),
    ("VNC",    "Ventral Nerve cord - Locates along the ventral side of the crustacean's body, coordinates sensory input and motor output for the body segments"),
]

families = [
    ("ACP",   "Adipokinetic hormone/Corazonin-related peptide"),
    ("ALP",   "Agatoxin-like peptide"),
    ("CCAP",   "Crustacean Cardioactive Peptide"),
    ("CHH",    "Crustacean Hyperglycemic Hormone"),
    ("CP2",    "Cerebral peptide 2"),
    ("CPRP",   "Crustacean hyperglycemic hormone Precursor Related Peptide"),
    ("DH",     "Diuretic Hormone"),
    ("DH31",   "Diuretic Hormone 31"),
    ("DH44",   "Diuretic Hormone 44"),
    ("ETH",    "Ecdysis Triggering Hormone"),
    ("EH",     "Eclosion Hormone"),
    ("ILP",     "Insulin-like Peptide"),
    ("MIH",    "Molt Inhibiting Hormone"),
    ("MOIH",   "Mandibular Organ Inhibiting Hormone"),
    ("NPF",    "Meuropeptide F"),
    ("PDH",    "Pigment Dispersing Hormone"),
    ("PRP",   "Precursor Related Peptide"),
    ("RPCH",   "Red Pigment Concentrating Hormone"),
    ("sNPF",   "short Neuropeptide F"),
]

tools = [
    ("Mass Spectrometry",     "Techniques to measure mass-to-charge ratios of peptide ions."),
    ("Peptide Property Calculator",    "Computes physicochemical properties of a peptide."),
    ("GRAVY",                 "Grand Average of Hydropathy indicates the overall hydrophobicity of a peptide; higher value = more hydrophobic."),
    ("Instability Index",     "Predicts whether a peptide is likely to be stable (< 40) or unstable (> 40) <i>in vitro</i>."),
    ("Isoelectric Point (pI)","The pH at which the peptide has no net electrical charge."),
    ("Net Charge (pH 7.0)",     "The overall positive or negative charge the peptide carries at neutral pH."),
    ("Aliphatic Index",       "Measures the volume of aliphatic side chains (A, V, I, L), which reflects thermal stability; higher value = more stable at higher temperatures."),
    ("Boman Index",           "Estimates a peptide's potential to bind to proteins; higher values suggest stronger or broader binding."),
    ("Peptide Sequence Alignment",    "Compares two peptide sequences to identify regions of similarity that may indicate functional, structural, or evolutionary relationships."),
    ("Type",                  "Global alignment aligns sequences end-to-end, while Local alignment finds the most similar subregions within the sequences."),
    ("Match",                 "Minimum exact match length to start alignment. Larger = faster but less sensitive."),
    ("Mismatch",              "The penalty applied when two aligned amino acids are different."),
    ("Gap Open",              "The penalty for introducing a new gap (insertion/deletion) in the alignment."),
    ("Gap Extend",            "The penalty for extending an existing gap by one more position."),
    #("BLAST",                 "Basic Local Alignment Search Tool for sequence similarity searches."),
    #("Compositional Bias",    "Adjusts scoring based on amino acid composition. Useful for short peptides."),
    #("E-value Threshold",     "Max acceptable probability that a hit is random. Lower = more stringent."),
    #("Gap Open",              "Cost for starting a gap. Higher = fewer gaps."),
    #("Gap Extend",            "Cost for extending a gap."),
    #("Matrix Choice",         "Substitution scoring (how similar two amino acids are)."),
    #("BLOSUM",                "(BLOcks SUbstitution Matrix) is a substitution matrix based on observed amino acid substitutions in conserved regions of protein families."),
    #("PAM",                   "(Point Accepted Mutation) is a matrix that estimates the likelihood of one amino acid mutating into another over evolutionary time."),
    #("SEG Filtering",         "Masks low-complexity regions (repeats). Useful to reduce false positives."),
    #("Score",                 "Overall alignment score based on your scoring matrix."),
    #("E-value",               "Lower values mean more significant hits; indicates the chance of a random match."),
    #("Percent Identity",      "Proportion of exact matches between your sequence and the hit.")
]

species = [
    ("Arm", "<i>Armadillidium</i> – Woodlouse"),
    ("Cbo", "<i>Cancer borealis</i> – Jonah crab or Stone crab"),
    ("Cirr", "<i>Cancer irroratus</i> – Atlantic rock crab"),
    ("Cmae", "<i>Carcinus maenas</i> – European green crab"),
    ("Cmag", "<i>Cancer magister</i> – Dungeness crab"),
    ("Cpag", "<i>Cancer pagurus</i> – Edible crab or Brown crab"),
    ("Cpro", "<i>Cancer productus</i> – Red rock crab"),
    ("Csap", "<i>Callinectes sapidus</i> – Blue crab"),
    ("Dpu", "<i>Daphnia pulex</i> – Common water flea"),
    ("Eis", "<i>Erimacrus isenbeckii</i> – Horsehair crab"),
    ("Eur", "<i>Eurydice</i> – Sand burrowing isopods"),
    ("HoA", "<i>Homarus americanus</i> – American lobster"),
    ("Lma", "<i>Lithodes maja</i> – Norway king crab"),
    ("Lva", "<i>Litopenaeus vannamei</i> – Pacific white shrimp"),
    ("Mens", "<i>Metapenaeus ensis</i> – Greasyback shrimp or Sand shrimp"),
    ("Mjap", "<i>Marsupenaeus japonicus</i> – Kuruma shrimp, Kuruma prawn, or Japanese tiger prawn"),
    ("Mlan", "<i>Macrobrachium lanchesteri</i> – Freshwater prawn or Riceland prawn"),
    ("Mros", "<i>Macrobrachium rosenbergii</i> – Giant river prawn or Giant freshwater prawn"),
    ("Nnor", "<i>Nephrops norvegicus</i> – Norway lobster"),
    ("Oce", "<i>Ocypode ceratophthalmus</i> – Horned ghost crab"),
    ("Olim", "<i>Orconectes limosus</i> – Spinycheek crayfish"),
    ("Paz", "<i>Penaeus aztecus</i> – Brown shrimp"),
    ("Pbo", "<i>Pandalus borealis</i> – Northern prawn"),
    ("Pbou", "<i>Procambarus bouvieri</i> – Maxican crayfish"),
    ("Pcla", "<i>Procambarus clarkii</i> – Red swamp crayfish"),
    ("Pint", "<i>Panulirus interruptus</i> – California spiny lobster"),
    ("Pmon", "<i>Penaeus monodon</i> – Giant tiger prawn"),
    ("Ppro", "<i>Pugettia producta</i> – Northern kelp crab"),
    ("Spar", "<i>Scylla paramamosain</i> – Southeast Asia mud crab"),
    ("Sser", "<i>Scylla serrata</i> – Giant mud crab"),
    ("Sver", "<i>Sagmariasus verreauxi</i> – Rock lobster"),
]

# Helper to render one section
def render_section(title, entries):
    st.markdown(f'<div class="section-heading">{title}</div>', unsafe_allow_html=True)
    for term, definition in entries:
        st.markdown(f"""
        <div class="glossary-item">
          <div class="glossary-term">{term}</div>
          <div class="glossary-def"><p>{definition}</p></div>
        </div>
        """, unsafe_allow_html=True)

# Render each glossary section
render_section("Tissues", tissues)
render_section("Neuropeptide Family", families)
render_section("Tools", tools)
render_section("Species", species)


st.markdown("""
<div style="text-align: center; font-size:14px; color:#2a2541;">
  <em>Last update: Jul 2026</em>
</div>
""", unsafe_allow_html=True)

