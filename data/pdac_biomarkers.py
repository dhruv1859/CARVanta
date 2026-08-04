"""
CARVanta — PDAC Biomarker Master List
=====================================
Single source of truth for Pancreatic Ductal Adenocarcinoma (PDAC) biomarkers.

The project was reoriented from a multi-cancer CAR-T antigen tool to a
PDAC-only biomarker platform. Every data-driven tab reads (directly or via
the generated biomarker_database.csv) from this list.

Each biomarker carries:
  - name          : marker symbol / identifier
  - category       : biological category as reported in the literature
  - indication     : 'up' | 'down' | 'context' | 'neutral'
  - source_group   : the specimen / assay family it was curated under

NOTE: The `neural bridge` module is intentionally NOT driven by this file.
"""

# ─── Raw curated data ────────────────────────────────────────────────────────
# Format per line:  <name>\t<category>\t<indication-symbol>
# Indication symbols:  ↑ (up)  ↓ (down)  ↑/↓ or context (context)  — / Neutral

_RAW = {
"Serum Protein": r"""
CA19-9 :: Glycolipid/protein :: up
sTRA :: Glycolipid/protein :: up
CEA :: Protein :: up
CA125 (MUC16) :: Glycoprotein :: up
CA242 :: Glycoprotein :: up
Osteonectin :: Protein :: up
Osteopontin :: Protein :: up
DUPAN-2 :: Glycolipid antigen :: up
LAMC2 :: Protein (laminin) :: up
ULBP2 :: Protein :: up
sCD40L :: Protein :: up
LRG1 :: Protein :: up
C4BPA :: Protein (complement) :: up
Cofilin-1 :: Protein :: up
sgC1qR :: Protein receptor :: up
Trypsinogen-2 :: Enzyme precursor :: up
DKK1 :: Protein (Wnt inhibitor) :: up
THBS-2 :: Protein (Thrombospondin) :: up
THBS-1 :: Protein :: up
AGR2 :: Protein :: up
REG1A :: Protein :: up
REGIII :: Protein :: up
REG1B :: Protein :: up
REG4 :: Protein :: up
SYCN :: Protein :: up
LOXL2 :: Enzyme (lysyl oxidase) :: up
PARK7/DJ-1 :: Protein :: up
TTR (Transthyretin) :: Protein :: context
TTF1 :: Transcription factor :: up
TTF2 :: Transcription factor :: up
TTF3 :: Transcription factor :: up
GPNMB :: Protein :: up
PRX-1 (Peroxiredoxin) :: Antioxidant protein :: up
TFPI :: Protein :: up
TIMP-1 :: Protein (MMP inhibitor) :: up
MMP-9 :: Enzyme :: up
IGFBP-1 :: Binding protein :: up
IGFBP-2 :: Binding protein :: up
IGFBP-3 :: Binding protein :: up
MSLN (Mesothelin) :: Protein :: up
C5 :: Complement protein :: up
MMP-7 :: Enzyme :: up
Cathepsin-D :: Enzyme :: up
MMP-12 :: Enzyme :: up
OPG (Osteoprotegerin) :: Protein :: up
Kisspeptin :: Protein :: down
Galectin :: Protein :: up
MUC16 :: Glycoprotein :: up
MUC5AC :: Glycoprotein :: up
PAM4 :: Antibody marker :: up
HSP27 :: Heat shock protein :: up
CAM17.1 :: Antibody marker :: up
Fuc-Hpt :: Fucosylated glycoprotein :: up
SAA (Serum Amyloid A) :: Protein :: up
APN/CD13 :: Enzyme :: up
M2-PK :: Metabolic enzyme :: up
APOA2 :: Apolipoprotein :: up
APOC1 :: Apolipoprotein :: up
APOC2 :: Apolipoprotein :: up
APOE :: Apolipoprotein :: up
ITIH :: Protein inhibitor :: up
APOA1 :: Apolipoprotein :: context
APOL1 :: Apolipoprotein :: up
TGF-beta :: Growth factor :: up
VEGF :: Growth factor :: up
FGF-10 / KGF-2 :: Growth factor :: up
PDGF :: Growth factor :: up
TSGF :: Growth factor :: up
IP-10 (CXCL10) :: Cytokine/chemokine :: context
IL-6 :: Cytokine :: up
MIC-1 / GDF15 :: Cytokine :: up
IL-11 :: Cytokine :: up
YKL-40 :: Cytokine-like :: up
IL-8 :: Cytokine :: up
IL-10 :: Cytokine :: up
IL-1beta :: Cytokine :: up
OSM (Oncostatin M) :: Cytokine :: up
TNF-alpha :: Cytokine :: up
M-CSF :: Cytokine :: up
CXCL11 :: Chemokine :: context
SCF (Stem Cell Factor) :: Cytokine :: up
Eotaxin :: Chemokine :: up
HGF :: Cytokine :: up
MCP-1 (CCL2) :: Chemokine :: up
CXCL10 :: Chemokine :: context
CEACAM1 :: Adhesion molecule :: up
ICAM-1 :: Adhesion molecule :: up
""",

"Serum lncRNA": r"""
LINC-PINT :: lncRNA :: down
SNHG15 :: lncRNA :: up
LINC01238 :: lncRNA :: up
ABHD11-AS1 :: lncRNA :: up
HULC :: lncRNA :: up
UFC1 :: lncRNA :: up
""",

"Serum miRNA": r"""
miR-21 :: miRNA :: up
miR-25 :: miRNA :: up
miR-210-3p :: miRNA :: up
miR-29a :: miRNA :: up
miR-19a :: miRNA :: up
miR-210 :: miRNA :: up
miR-155 :: miRNA :: up
miR-499a-5p :: miRNA :: up
miR-125a-3p :: miRNA :: down
miR-6893-5p :: miRNA :: up
miR-125b-1-3p :: miRNA :: down
miR-6075 :: miRNA :: up
miR-6836-3p :: miRNA :: up
miR-1469 :: miRNA :: up
miR-6729-5p :: miRNA :: up
miR-575 :: miRNA :: up
miR-204-3p :: miRNA :: down
miR-6820-5p :: miRNA :: up
miR-4294 :: miRNA :: up
miR-4476 :: miRNA :: up
miR-4792 :: miRNA :: up
miR-196a :: miRNA :: up
miR-18a :: miRNA :: up
miR-10b :: miRNA :: up
miR-106b :: miRNA :: up
miR-642-3p :: miRNA :: up
miR-885-5p :: miRNA :: up
miR-22-3p :: miRNA :: up
miR-34a :: miRNA :: down
miR-191 :: miRNA :: up
miR-451a :: miRNA :: down
miR-121-5p :: miRNA :: up
miR-30c :: miRNA :: down
miR-483-5p :: miRNA :: up
miR-1290 :: miRNA :: up
miR-24 :: miRNA :: up
miR-134 :: miRNA :: down
miR-146a :: miRNA :: context
miR-378 :: miRNA :: up
miR-484 :: miRNA :: up
miR-628-4p :: miRNA :: up
miR-1825 :: miRNA :: up
miR-1246 :: miRNA :: up
miR-482-3p :: miRNA :: context
miR-16 :: miRNA :: down
miR-27a-3p :: miRNA :: up
miR-192 :: miRNA :: context
miR-642b-3p :: miRNA :: up
miR-492 :: miRNA :: up
miR-663a :: miRNA :: up
miR-194 :: miRNA :: down
miR-223 :: miRNA :: up
miR-774-5p :: miRNA :: up
miR-409-3p :: miRNA :: down
miR-128-3p :: miRNA :: down
miR-20a :: miRNA :: up
miR-27a :: miRNA :: up
miR-29c :: miRNA :: down
miR-30a-5p :: miRNA :: down
miR-323-3p :: miRNA :: up
miR-345 :: miRNA :: down
""",
"Serum Liquid Biopsy": r"""
GPC1 :: Exosome :: up
miR-10b :: Exosome :: up
miR-30c :: Exosome :: down
miR-181a :: Exosome :: up
miR-let7a :: Exosome :: down
miR-17-5p :: Exosome :: up
miR-21 :: Exosome :: up
miR-1246 :: Exosome :: up
miR-4644 :: Exosome :: up
miR-3976 :: Exosome :: up
miR-4306 :: Exosome :: up
KRAS (mutation) :: ctDNA :: up
ADAMTS1 :: ctDNA :: up
BNC1 :: ctDNA :: up
CAPI+/CD45- :: CTC :: up
CK+ (Cytokeratin) :: CTC :: up
CEA+ :: CTC :: up
CD45-/DAPI+/CEP8 :: CTC :: up
CD45 :: CTC :: down
CCK19 :: CTC :: up
Pdx-1 :: CTC :: up
KRAS mutation (CTC) :: CTC :: up
CEP8 :: CTC :: up
CK :: CTC :: up
DAPI :: CTC :: neutral
Chromosome 8 :: CTC :: up
Folate-receptor positive CTCs :: CTC :: up
""",

"Urinary": r"""
LYVE1 :: Protein :: up
REG1A :: Protein :: up
TTF1 :: Protein :: up
TIMP1 :: Protein :: up
MMP-2 :: Protein :: up
NGAL :: Protein :: up
PGE2 metabolites :: Protein :: up
CD59 :: Protein :: up
ANXA2 :: Protein :: up
21 kDa gelsolin fragment :: Protein :: up
S100A9 :: Protein :: up
KRAS mutation (UcfDNA) :: Liquid biopsy :: up
miR-3940-5p :: Exosomal miRNA :: up
miR-8069 :: Exosomal miRNA :: up
miR-143 :: miRNA (RNA) :: down
miR-223 :: miRNA (RNA) :: up
miR-30e :: miRNA (RNA) :: down
miR-1246 :: miRNA (RNA) :: up
Calcium :: Metallomics :: up
Magnesium :: Metallomics :: up
VOCs :: Other :: up
""",

"Pancreatic Juice": r"""
CA19-9 :: Protein :: up
MIC-1 :: Protein :: up
NGAL :: Protein :: up
CEA :: Protein :: up
AMYP :: Protein :: up
PRSS1 :: Protein :: up
GP2-1 :: Protein :: up
CCDC132 :: Protein :: up
REG1A :: Protein :: up
REG1B :: Protein :: up
REG3A :: Protein :: up
LIPRP2 :: Protein :: up
KL-6/MUC1 :: Protein :: up
CPA5 :: Protein :: up
LIPRP1 (inactive) :: Protein :: up
KLK1 :: Protein :: up
HBD :: Protein :: up
TTR :: Protein :: up
S100P :: Protein :: up
MMP-9 :: Protein :: up
MMP-7 :: Protein :: up
DJ-1 :: Protein :: up
A1BG :: Protein :: up
PAP-1 :: Protein :: up
AGR2 :: Protein :: up
IL-8 :: Protein :: up
Cathepsin E :: Protein :: up
miR-21 :: RNA (miRNA) :: up
miR-155 :: RNA (miRNA) :: up
miR-205 :: RNA (miRNA) :: up
miR-210 :: RNA (miRNA) :: up
miR-492 :: RNA (miRNA) :: up
miR-1427 :: RNA (miRNA) :: up
Mesothelin (mRNA) :: RNA :: up
hTERT :: RNA (other) :: up
Telomerase activity :: RNA (other) :: up
CEACAM1 :: Liquid biopsy (Exosome) :: up
CEACAM5 :: Liquid biopsy (Exosome) :: up
Tenascin C :: Liquid biopsy (Exosome) :: up
MMP7 :: Liquid biopsy (Exosome) :: up
LAMB3 :: Liquid biopsy (Exosome) :: up
LAMC2 :: Liquid biopsy (Exosome) :: up
MUC1 :: Liquid biopsy (Exosome) :: up
MUC4 :: Liquid biopsy (Exosome) :: up
MUC5AC :: Liquid biopsy (Exosome) :: up
MUC6 :: Liquid biopsy (Exosome) :: up
MUC16 :: Liquid biopsy (Exosome) :: up
CFTR :: Liquid biopsy (Exosome) :: up
MDR1 :: Liquid biopsy (Exosome) :: up
ex-miR-21 :: Liquid biopsy (Exosomal miRNA) :: up
ex-miR-155 :: Liquid biopsy (Exosomal miRNA) :: up
KRAS (methylated DNA) :: Liquid biopsy (DNA) :: up
ppENK (methylated DNA) :: Liquid biopsy (DNA) :: down
p16 (methylated DNA) :: Liquid biopsy (DNA) :: down
Cyclin D2 (methylated DNA) :: Liquid biopsy (DNA) :: up
FOXE1 (methylated DNA) :: Liquid biopsy (DNA) :: down
NPTX2 (methylated DNA) :: Liquid biopsy (DNA) :: down
TFPI2 (methylated DNA) :: Liquid biopsy (DNA) :: down
CD1D (methylated DNA) :: Liquid biopsy (DNA) :: down
KCNK12 (methylated DNA) :: Liquid biopsy (DNA) :: down
CLEC11A (methylated DNA) :: Liquid biopsy (DNA) :: down
NDRG4 (methylated DNA) :: Liquid biopsy (DNA) :: down
IKZF1 (methylated DNA) :: Liquid biopsy (DNA) :: down
PKRCB (methylated DNA) :: Liquid biopsy (DNA) :: down
MUC1 (methylated DNA) :: Liquid biopsy (DNA) :: up
MUC2 (methylated DNA) :: Liquid biopsy (DNA) :: up
MUC4 (methylated DNA) :: Liquid biopsy (DNA) :: up
""",

"Pancreatic Cyst Fluid": r"""
CEA :: Protein :: up
Glucose :: Protein :: up
MUC4 :: Protein :: up
PGE2 :: Protein :: up
IL-1B :: Protein :: up
PGE synthetase 2 :: Protein :: up
IL-4 :: Protein :: up
CA72-4 :: Protein :: up
sFASL :: Protein :: up
MMP9 :: Protein :: up
AREG (Amphiregulin) :: Protein :: up
SPINK1 :: Protein :: up
mAB Das-1 :: Protein :: up
IL-10 :: Protein :: up
GM-CSF :: Protein :: up
MUC1 :: Protein :: up
MUC2 :: Protein :: up
MUC5AC :: Protein :: up
miR-21 :: RNA (miRNA) :: up
miR-221 :: RNA (miRNA) :: up
miR-18a :: RNA (miRNA) :: up
miR-24 :: RNA (miRNA) :: up
miR-30a-3p :: RNA (miRNA) :: up
miR-92a :: RNA (miRNA) :: up
miR-99b :: RNA (miRNA) :: up
miR-106b :: RNA (miRNA) :: up
miR-142-3p :: RNA (miRNA) :: up
miR-342-3p :: RNA (miRNA) :: up
miR-532-3p :: RNA (miRNA) :: up
KRAS mutations :: DNA (Other) :: up
GNAS mutations :: DNA (Other) :: up
""",

"Salivary": r"""
HOTAIR :: RNA (LncRNA) :: up
PVT1 :: RNA (LncRNA) :: up
miR-21 :: RNA (miRNA) :: up
miR-23a :: RNA (miRNA) :: up
miR-23b :: RNA (miRNA) :: up
miR-29c :: RNA (miRNA) :: down
miR-1246 :: RNA (miRNA) :: up
miR-4644 :: RNA (miRNA) :: up
miR-34a :: RNA (miRNA) :: down
miR-155 :: RNA (miRNA) :: up
miR-200b :: RNA (miRNA) :: down
miR-376a :: RNA (miRNA) :: up
miR-216 :: RNA (miRNA) :: up
miR-940 :: RNA (miRNA) :: up
miR-3679-5p :: RNA (miRNA) :: up
miR-17 :: RNA (miRNA) :: up
miR-181b :: RNA (miRNA) :: up
miR-196a :: RNA (miRNA) :: up
Alanine :: Salivary polyamine :: up
N1-acetylspermidine :: Salivary polyamine :: up
2-oxobutyrate :: Salivary polyamine :: up
2-hydroxybutyrate :: Salivary polyamine :: up
""",

"Biliary": r"""
VEGF :: Protein :: up
CA19-9 :: Protein :: up
CA125 :: Protein :: up
CA72-4 :: Protein :: up
CEA :: Protein :: up
sLR11 :: Protein :: up
MUC4 :: Protein :: up
IGF-1 :: Protein :: up
NGAL :: Protein :: up
CEAM6 :: Protein :: up
LG3BP :: Protein :: up
MMP7 :: Protein :: up
MUC5B :: Protein :: up
MCM5 :: Protein :: up
Trypsinogen-1 :: Protein :: up
Trypsinogen-2 :: Protein :: up
TFPI2 (methylated DNA) :: Liquid biopsy :: up
NPTX2 (methylated DNA) :: Liquid biopsy :: up
CCND2 (methylated DNA) :: Liquid biopsy :: up
miR-10b :: RNA (miRNA) :: up
miR-106b :: RNA (miRNA) :: up
miR-30c :: RNA (miRNA) :: up
miR-155 :: RNA (miRNA) :: up
miR-212 :: RNA (miRNA) :: up
miR-1247 :: RNA (miRNA) :: up
miR-200a :: RNA (miRNA) :: down
miR-200b :: RNA (miRNA) :: down
""",

"Faecal": r"""
Adnab-9 :: Protein :: up
miR-181b :: RNA (miRNA) :: up
miR-210 :: RNA (miRNA) :: up
miR-155 :: RNA (miRNA) :: up
miR-216a :: RNA (miRNA) :: up
miR-196a :: RNA (miRNA) :: up
miR-143 :: RNA (miRNA) :: down
Mutant KRAS :: Liquid biopsy :: up
mBMP3 :: Liquid biopsy (methylated DNA) :: up
""",
"Structural Variant Gene": r"""
RB1 :: Tumor suppressor :: down
MDC1 :: DNA damage response :: down
SMARCB1 :: Tumor suppressor :: down
RPLP0P2 :: Pseudogene (Not biomarker) :: neutral
KEAP1 :: Oxidative stress regulator :: up
TESK2 :: Kinase (Not validated) :: neutral
SLC4A4 :: Transporter (Not validated) :: neutral
RPS6KA4 :: Oncogenic kinase :: up
GJA1 :: Gap junction protein (not biomarker) :: neutral
TFG :: Oncogenic fusion protein :: up
RPS19 :: Ribosomal protein (not biomarker) :: neutral
PPP2R1A :: Tumor suppressor :: down
CHEK1 :: DNA damage checkpoint :: up
AKT3 :: Oncogene :: up
TRIM24 :: Oncogene :: up
AKT1 :: Oncogene :: up
SOX9 :: Developmental oncogene :: up
B2M :: Immune regulator, cancer progression :: up
TP63 :: p53 family oncogene :: up
ICOSLG :: Immune checkpoint :: up
UNC13C :: Synaptic vesicle priming (Not biomarker) :: neutral
ZNF284 :: Transcription factor (Not validated) :: neutral
P3H2 :: Hydroxylase (Not validated) :: neutral
RECQL :: DNA repair, tumor suppressor :: down
DDX10 :: Oncogene :: up
SND1 :: Oncogene :: up
NUP93 :: Nuclear pore protein (oncogenic role) :: up
EML4 :: Oncogenic fusion partner :: up
INPP4B :: Tumor suppressor :: down
SHTN1 :: Axon guidance (Not biomarker) :: neutral
EWSR1 :: Fusion oncogene :: up
TP53 :: Tumor suppressor :: down
MAOB :: Metabolic enzyme (Not biomarker) :: neutral
GIPR :: GPCR (Not biomarker) :: neutral
AIRE :: Immune regulator (Not biomarker) :: neutral
AGAP1 :: GTPase regulator (Not biomarker) :: neutral
PIK3R1 :: Oncogene :: up
CBARP :: Calcium-binding protein (Not biomarker) :: neutral
CD79A :: Immune signaling (oncogenic role) :: up
BRIP1 :: DNA repair, tumor suppressor :: down
HMGXB4 :: Transcription factor (not validated) :: neutral
TSPAN9 :: Membrane protein (not validated) :: neutral
RAD21 :: DNA repair/oncogene :: up
AGMO :: Metabolic enzyme (not biomarker) :: neutral
H3C3 :: Chromatin modifier (oncogenic) :: up
H3C4 :: Chromatin modifier (oncogenic) :: up
H3C6 :: Chromatin modifier (oncogenic) :: up
ZRSR2 :: Splicing factor, tumor suppressor :: down
INSR :: Growth signaling oncogene :: up
BRAF :: Oncogene :: up
GRIN2B :: Receptor (not biomarker) :: neutral
UBAC1 :: Ubiquitin pathway (not biomarker) :: neutral
SMARCA4 :: Tumor suppressor :: down
ZZZ3 :: Transcription regulator (not biomarker) :: neutral
FUBP1 :: Oncogene/transcription factor :: up
FAT1 :: Tumor suppressor :: down
ATM :: DNA damage checkpoint, tumor suppressor :: down
CTRC :: Protease (not biomarker) :: neutral
BAP1 :: Tumor suppressor :: down
ATR :: DNA damage checkpoint :: down
EZH2 :: Epigenetic oncogene :: up
PTPRT :: Tumor suppressor :: down
RET :: Oncogene :: up
C2CD2 :: Unknown role (not biomarker) :: neutral
BRCA1 :: Tumor suppressor :: down
KRI1 :: Ribosome biogenesis (not biomarker) :: neutral
GLI1 :: Hedgehog pathway oncogene :: up
PHF7 :: Transcription regulator (not biomarker) :: neutral
BRCA2 :: Tumor suppressor :: down
BABAM1 :: DNA repair/tumor suppressor :: down
DNER :: Signaling protein (not biomarker) :: neutral
RAC2 :: Oncogenic GTPase :: up
KIF13B :: Motor protein (not biomarker) :: neutral
CIC :: Tumor suppressor :: down
JAK3 :: Oncogenic tyrosine kinase :: up
SPMIP11 :: Not validated :: neutral
DUSP4 :: Tumor suppressor/regulator :: down
UPF1 :: RNA surveillance, tumor suppressor :: down
PBRM1 :: Tumor suppressor (SWI/SNF complex) :: down
IFNGR1 :: Immune signaling, tumor suppressor role :: down
NCOA3 :: Oncogenic coactivator :: up
NCOA4 :: Autophagy adaptor, oncogenic :: up
TET1 :: DNA demethylase, tumor suppressor :: down
RAD51B :: DNA repair, tumor suppressor :: down
ANKFN1 :: Not validated :: neutral
AEBP2 :: Transcriptional repressor (not validated) :: neutral
SDHAF2 :: Tumor suppressor (metabolism) :: down
CSDE1 :: RNA-binding oncogene :: up
RARA :: Nuclear receptor, oncogenic role :: up
PDZRN3 :: Not validated :: neutral
CD44 :: Stemness/cell adhesion, oncogene :: up
AMER1 :: Tumor suppressor (Wnt pathway) :: down
PRKN :: Tumor suppressor :: down
KANK1 :: Not validated :: neutral
LIN37 :: Cell cycle regulator (not validated) :: neutral
DOT1L :: Oncogenic epigenetic regulator :: up
GREB1L :: Not validated :: neutral
TMPRSS2 :: Oncogene (fusion driver) :: up
ADCY1 :: Not validated :: neutral
CENPA :: Chromatin/centromere oncogene :: up
ADCY6 :: Not validated :: neutral
EGFR :: Oncogene :: up
RECQL4 :: DNA repair/tumor suppressor :: down
NSD3 :: Oncogenic histone methyltransferase :: up
SLX4 :: DNA repair tumor suppressor :: down
NSD1 :: Oncogenic histone methyltransferase :: up
NSD2 :: Oncogenic histone methyltransferase :: up
RICTOR :: Oncogene (mTOR pathway) :: up
MGAT1 :: Not validated :: neutral
LDLR :: Metabolic receptor (not biomarker) :: neutral
MON2 :: Not validated :: neutral
CDKN2B :: Tumor suppressor :: down
NPM1 :: Oncogene (frequently mutated) :: up
CDKN2A :: Tumor suppressor :: down
CARD8 :: Inflammasome regulator (not biomarker) :: neutral
CIMAP1D :: Not validated :: neutral
STAT3 :: Oncogenic transcription factor :: up
VEGFA :: Angiogenesis oncogene :: up
NFIA :: Transcription factor (not validated) :: neutral
AXL :: Oncogene :: up
GOPC :: Oncogene :: up
RIPOR2 :: Oncogene :: down
IRS2 :: Oncogene :: up
CEP128 :: Oncogene :: down
STK11 :: Tumor Suppressor :: up
ZNF83 :: Oncogene :: down
CDH1 :: Tumor Suppressor :: up
EP300 :: Tumor Suppressor :: up
ARID2 :: Tumor Suppressor :: up
ROS1 :: Oncogene :: up
MEN1 :: Tumor Suppressor :: up
LMO1 :: Oncogene :: up
RNF43 :: Tumor Suppressor :: up
SLC30A6 :: Oncogene :: down
MAP2K4 :: Tumor Suppressor :: up
MAP2K2 :: Oncogene :: up
DGAT1 :: Oncogene :: down
HGF :: Oncogene :: up
TAP2 :: Tumor Suppressor :: up
ARID5B :: Tumor Suppressor :: up
TAP1 :: Tumor Suppressor :: up
TSC2 :: Tumor Suppressor :: up
VRK3 :: Oncogene :: down
ATP1B1 :: Oncogene :: down
FOXP1 :: Oncogene :: up
MSH6 :: DNA Repair/Tumor Suppressor :: up
SRSF2 :: Oncogene :: up
PGR :: Oncogene :: up
RAF1 :: Oncogene :: up
EMID1 :: Oncogene :: down
FKBP5 :: Oncogene :: down
NOTCH2 :: Oncogene :: up
KMT2D :: Tumor Suppressor :: up
CSF1R :: Oncogene :: up
DNMT1 :: Oncogene :: up
NOTCH1 :: Oncogene :: up
CBFB :: Tumor Suppressor :: up
KMT2A :: Tumor Suppressor :: up
MAX :: Oncogene :: up
KMT2C :: Tumor Suppressor :: up
NOTCH4 :: Oncogene :: up
KMT2B :: Tumor Suppressor :: up
CORO1B :: Oncogene :: down
COP1 :: Tumor Suppressor :: up
ADGRG7 :: Oncogene :: down
TNFRSF14 :: Tumor Suppressor :: up
ZFHX3 :: Tumor Suppressor :: up
SMAD4 :: Tumor Suppressor :: up
SMAD3 :: Tumor Suppressor :: up
IDH1 :: Oncogene :: up
TNFRSF10B :: Tumor Suppressor :: down
PALB2 :: Tumor Suppressor :: up
PTPRD :: Tumor Suppressor :: up
CDK8 :: Oncogene :: up
CDK4 :: Oncogene :: up
MAFG :: Oncogene :: down
NF1 :: Tumor Suppressor :: up
TUBGCP3 :: Oncogene :: down
REEP6 :: Oncogene :: down
TCF3 :: Oncogene :: up
NF2 :: Tumor Suppressor :: up
MAP3K13 :: Oncogene :: up
MAP3K14 :: Oncogene :: up
FGFR3 :: Oncogene :: up
FGFR2 :: Oncogene :: up
FGFR1 :: Oncogene :: up
BCL2L1 :: Oncogene :: up
BMPR1A :: Tumor Suppressor :: up
NFE2L2 :: Oncogene :: up
KDM5A :: Oncogene :: up
ALK :: Oncogene :: up
CFAP418-AS1 :: Non-coding RNA :: down
ZNF770 :: Oncogene :: down
FLT3 :: Oncogene :: up
FLT4 :: Oncogene :: up
ARRB1 :: Oncogene :: down
PIK3C2G :: Oncogene :: up
ELAVL2 :: Oncogene :: down
TRIM69 :: Oncogene :: down
WDR7 :: Oncogene :: down
POLE :: DNA Repair/Tumor Suppressor :: up
SGCG :: Oncogene :: down
KDM6A :: Tumor Suppressor :: up
CERS5 :: Oncogene :: down
TRPC6 :: Oncogene :: down
DIPK2B :: Oncogene :: down
DIS3 :: Tumor Suppressor :: up
DCXR :: Oncogene :: down
NRG1 :: Oncogene :: up
ARID1A :: Tumor Suppressor :: up
UPK3A :: Oncogene :: down
ARID1B :: Tumor Suppressor :: up
TGFBR1 :: Tumor Suppressor :: up
TGFBR2 :: Tumor Suppressor :: up
ETV6 :: Tumor Suppressor :: up
DNM2 :: Oncogene :: up
IRF4 :: Oncogene :: up
PEX6 :: Oncogene :: down
CAT :: Antioxidant/Tumor Suppressor :: down
CDHR3 :: Oncogene (candidate) :: down
PIK3C3 :: Oncogene :: up
NSRP1 :: RNA-binding/regulatory :: down
MET :: Oncogene :: up
LUC7L2 :: RNA-binding/regulatory :: down
KDM7A :: Epigenetic regulator :: down
SLC24A2 :: Transporter :: down
SMARCD1 :: Chromatin remodeler :: up
NUTM1 :: Oncogene (fusion driver) :: up
ROCK1 :: Oncogene candidate :: down
DNAH8 :: Motor protein :: down
MLLT1 :: Oncogene (fusion partner) :: up
ASAP2 :: Signaling regulator :: down
ASB17 :: Adapter protein :: down
PPM1D :: Oncogene :: up
MALT1 :: Oncogene :: up
CDC42 :: Oncogene (Rho GTPase family) :: up
RAB25 :: Oncogene candidate :: down
ERBB3 :: Oncogene :: up
NT5DC2 :: Oncogene candidate :: down
POLD1 :: DNA repair/Tumor suppressor :: up
ERBB2 :: Oncogene :: up
DROSHA :: microRNA biogenesis regulator :: up
MAPK4 :: Oncogene candidate :: down
SMARCE1 :: Chromatin remodeler :: up
NTRK1 :: Oncogene :: up
SLC12A3 :: Transporter :: down
NHERF2 :: Scaffold protein :: down
NDUFA3 :: Mitochondrial enzyme :: down
MGA :: Transcriptional regulator / Tumor suppressor :: up
NTRK3 :: Oncogene :: up
TBX3 :: Oncogene (developmental regulator) :: up
TSHR :: Oncogene (endocrine cancers) :: up
RAD50 :: DNA repair / Tumor suppressor :: up
CAPN11 :: Protease (non-canonical) :: down
H3-5 :: Epigenetic regulator :: up
APC :: Tumor suppressor :: up
CARM1 :: Epigenetic regulator :: up
ERCC2 :: DNA repair enzyme :: up
RPS6KB2 :: Oncogene (mTOR pathway effector) :: up
ASXL2 :: Epigenetic regulator :: up
ARB2A :: Candidate gene :: down
PDCD1 :: Immune checkpoint :: up
TEK :: Oncogene / Angiogenesis regulator :: up
BCOR :: Tumor suppressor :: up
KCNK3 :: Channel protein :: down
""",
"Mutated Gene": r"""
RB1 :: Tumor Suppressor :: down
MDC1 :: Tumor Suppressor :: down
ARAF :: Oncogene :: up
PREX2 :: Oncogene :: up
SOX17 :: Tumor Suppressor :: down
PPP4R2 :: Tumor Suppressor :: down
MYC :: Oncogene :: up
AKT2 :: Oncogene :: up
AKT3 :: Oncogene :: up
AKT1 :: Oncogene :: up
PRKCI :: Oncogene :: up
DAXX :: Tumor Suppressor :: down
MEF2B :: Oncogene :: up
DICER1 :: Tumor Suppressor :: down
KNSTRN :: Oncogene :: up
NUP93 :: Tumor Suppressor :: down
AR :: Oncogene :: up
MTAP :: Tumor Suppressor :: down
PRKAR1A :: Tumor Suppressor :: down
PRKD1 :: Oncogene :: up
MAPKAP1 :: Oncogene :: up
PRDM14 :: Oncogene :: up
GATA3 :: Tumor Suppressor :: down
BCL10 :: Oncogene :: up
GATA2 :: Tumor Suppressor :: down
GATA1 :: Tumor Suppressor :: down
GRIN2A :: Tumor Suppressor :: down
TERT :: Oncogene :: up
NTHL1 :: Tumor Suppressor :: down
RAD21 :: Oncogene :: up
PLCG2 :: Oncogene :: up
NKX2-1 :: Oncogene :: up
BARD1 :: Tumor Suppressor :: down
LYN :: Oncogene :: up
JUN :: Oncogene :: up
CREBBP :: Tumor Suppressor :: down
PLK2 :: Tumor Suppressor :: down
BRAF :: Oncogene :: up
H1-2 :: Tumor Suppressor :: down
CYLD :: Tumor Suppressor :: down
AGO2 :: Oncogene :: up
FAT1 :: Tumor Suppressor :: down
REL :: Oncogene :: up
CDK12 :: Tumor Suppressor :: down
EZH1 :: Oncogene :: up
EZH2 :: Oncogene :: up
RET :: Oncogene :: up
CDKN1A :: Tumor Suppressor :: down
SETD2 :: Tumor Suppressor :: down
CDKN1B :: Tumor Suppressor :: down
CTCF :: Tumor Suppressor :: down
GLI1 :: Oncogene :: up
PHF6 :: Tumor Suppressor :: down
BBC3 :: Tumor Suppressor :: down
MED12 :: Tumor Suppressor :: down
NUF2 :: Oncogene :: up
CTLA4 :: Tumor Suppressor :: down
ELOC :: Tumor Suppressor :: down
CIC :: Tumor Suppressor :: down
JAK2 :: Oncogene :: up
IKBKE :: Oncogene :: up
JAK3 :: Oncogene :: up
JAK1 :: Oncogene :: up
DUSP4 :: Tumor Suppressor :: down
UPF1 :: Tumor Suppressor :: down
IFNGR1 :: Tumor Suppressor :: down
TET2 :: Tumor Suppressor :: down
RRAS2 :: Oncogene :: up
TET1 :: Tumor Suppressor :: down
PAX5 :: Tumor Suppressor :: down
NCOR1 :: Tumor Suppressor :: down
RARA :: Oncogene :: up
POT1 :: Tumor Suppressor :: down
PPARG :: Tumor Suppressor :: down
FH :: Tumor Suppressor :: down
GPS2 :: Tumor Suppressor :: down
CENPA :: Oncogene :: up
EGFR :: Oncogene :: up
RECQL4 :: Tumor Suppressor :: down
NSD3 :: Oncogene :: up
NRAS :: Oncogene :: up
H3C13 :: Oncogene :: up
NSD1 :: Oncogene :: up
H3C11 :: Oncogene :: up
NSD2 :: Oncogene :: up
SPOP :: Tumor Suppressor :: down
H3C10 :: Oncogene :: up
PMS2 :: Tumor Suppressor :: down
RICTOR :: Oncogene :: up
SF3B1 :: Oncogene :: up
PMS1 :: Tumor Suppressor :: down
BRD4 :: Oncogene :: up
CDKN2B :: Tumor Suppressor :: down
CDKN2C :: Tumor Suppressor :: down
CDKN2A :: Tumor Suppressor :: down
RYBP :: Tumor Suppressor :: down
WT1 :: Tumor Suppressor :: down
INHA :: Oncogene :: up
CRLF2 :: Oncogene :: up
CSF3R :: Oncogene :: up
MRE11 :: Tumor Suppressor :: down
IRS1 :: Oncogene :: up
IRS2 :: Oncogene :: up
STK19 :: Oncogene :: up
MSI1 :: Oncogene :: up
MSI2 :: Oncogene :: up
FGF3 :: Oncogene :: up
FGF4 :: Oncogene :: up
STK11 :: Tumor Suppressor :: down
CYSLTR2 :: Oncogene :: up
CDH1 :: Tumor Suppressor :: down
SESN2 :: Tumor Suppressor :: down
PIM1 :: Oncogene :: up
NBN :: Tumor Suppressor :: down
KMT5A :: Oncogene :: up
ROS1 :: Oncogene :: up
MEN1 :: Tumor Suppressor :: down
RNF43 :: Tumor Suppressor :: down
MAP2K4 :: Tumor Suppressor :: down
MAP2K1 :: Oncogene :: up
MAP2K2 :: Oncogene :: up
FBXW7 :: Tumor Suppressor :: down
EIF1AX :: Oncogene :: up
TAP2 :: Tumor Suppressor :: down
TAP1 :: Tumor Suppressor :: down
MITF :: Oncogene :: up
FOXP1 :: Oncogene :: up
MSH6 :: Tumor Suppressor :: down
SMO :: Oncogene :: up
MSH2 :: Tumor Suppressor :: down
MSH3 :: Tumor Suppressor :: down
ERF :: Tumor Suppressor :: down
PGR :: Oncogene :: up
ERG :: Oncogene :: up
NOTCH2 :: Oncogene :: up
CD274 :: Oncogene :: up
CSF1R :: Oncogene :: up
KMT2D :: Tumor Suppressor :: down
NOTCH3 :: Oncogene :: up
DNMT1 :: Oncogene :: up
BLM :: Tumor Suppressor :: down
NOTCH1 :: Oncogene :: up
CBFB :: Tumor Suppressor :: down
KMT2A :: Oncogene :: up
MAX :: Oncogene :: up
CUL3 :: Tumor Suppressor :: down
ANKRD11 :: Tumor Suppressor :: down
NOTCH4 :: Oncogene :: up
KMT2C :: Tumor Suppressor :: down
KMT2B :: Oncogene :: up
VTCN1 :: Oncogene :: up
CYP19A1 :: Oncogene :: up
FOXO1 :: Tumor Suppressor :: down
BCL2L11 :: Tumor Suppressor :: down
SOCS1 :: Tumor Suppressor :: down
ATXN7 :: Tumor Suppressor :: down
ABL1 :: Oncogene :: up
SMYD3 :: Oncogene :: up
MCL1 :: Oncogene :: up
CD276 :: Oncogene :: up
FANCA :: Tumor Suppressor :: down
FANCC :: Tumor Suppressor :: down
PALB2 :: Tumor Suppressor :: down
PTPRD :: Tumor Suppressor :: down
CDK8 :: Oncogene :: up
CDK6 :: Oncogene :: up
BCL6 :: Oncogene :: up
CDK4 :: Oncogene :: up
RHEB :: Oncogene :: up
NF1 :: Tumor Suppressor :: down
BCL2 :: Oncogene :: up
MDM2 :: Oncogene :: up
MDM4 :: Oncogene :: up
NF2 :: Tumor Suppressor :: down
MAP3K13 :: Oncogene :: up
MYD88 :: Oncogene :: up
BCL2L1 :: Oncogene :: up
NFE2L2 :: Oncogene :: up
ALK :: Oncogene :: up
FLT1 :: Oncogene :: up
FLT3 :: Oncogene :: up
FLT4 :: Oncogene :: up
PTEN :: Tumor Suppressor :: down
PIK3CD :: Oncogene :: up
PIK3C2G :: Oncogene :: up
PIK3CB :: Oncogene :: up
CDC73 :: Tumor Suppressor :: down
PIK3CG :: Oncogene :: up
PPP6C :: Tumor Suppressor :: down
DNMT3B :: Oncogene :: up
NKX3-1 :: Tumor Suppressor :: down
DIS3 :: Tumor Suppressor :: down
ATRX :: Tumor Suppressor :: down
DNMT3A :: Oncogene :: up
TRAF2 :: Oncogene :: up
FOXL2 :: Oncogene :: up
PTP4A1 :: Oncogene :: up
TRAF7 :: Oncogene :: up
PIK3CA :: Oncogene :: up
PIK3C3 :: Oncogene :: up
TOP1 :: Oncogene :: up
SOS1 :: Oncogene :: up
MET :: Oncogene :: up
BIRC3 :: Oncogene :: up
SMARCD1 :: Oncogene :: up
CEBPA :: Tumor Suppressor :: down
SRC :: Oncogene :: up
U2AF1 :: Oncogene :: up
PPM1D :: Oncogene :: up
MALT1 :: Oncogene :: up
CDC42 :: Oncogene :: up
DNAJB1 :: Oncogene :: up
FIP1L1 :: Oncogene :: up
E2F3 :: Oncogene :: up
FYN :: Oncogene :: up
EIF4E :: Oncogene :: up
SH2B3 :: Tumor Suppressor :: down
NTRK1 :: Oncogene :: up
NTRK2 :: Oncogene :: up
MGA :: Tumor Suppressor :: down
NTRK3 :: Oncogene :: up
PTPN11 :: Oncogene :: up
KLF4 :: Tumor Suppressor :: down
MTOR :: Oncogene :: up
TBX3 :: Oncogene :: up
PNRC1 :: Oncogene :: up
ASXL1 :: Tumor Suppressor :: down
RAD52 :: Tumor Suppressor :: down
RAD50 :: Tumor Suppressor :: down
KLF5 :: Oncogene :: up
RAD51 :: Tumor Suppressor :: down
APC :: Tumor Suppressor :: down
ASXL2 :: Tumor Suppressor :: down
PDCD1 :: Tumor Suppressor :: down
BCOR :: Tumor Suppressor :: down
EIF4A2 :: Oncogene :: up
ERRFI1 :: Tumor Suppressor :: down
SMARCB1 :: Tumor Suppressor :: down
KEAP1 :: Tumor Suppressor :: down
IKZF1 :: Tumor Suppressor :: down
CRKL :: Oncogene :: up
RPS6KA4 :: Oncogene :: up
SOX2 :: Oncogene :: up
PPP2R1A :: Tumor Suppressor :: down
CHEK2 :: Tumor Suppressor :: down
CHEK1 :: Tumor Suppressor :: down
KDR :: Oncogene :: up
SOX9 :: Oncogene :: up
EPHB1 :: Oncogene :: up
B2M :: Tumor Suppressor :: down
TP63 :: Oncogene :: up
ICOSLG :: Oncogene :: up
EPHA5 :: Oncogene :: up
ACVR1 :: Oncogene :: up
EPHA7 :: Oncogene :: up
HLA-B :: Tumor Suppressor :: down
RECQL :: Tumor Suppressor :: down
HNF1A :: Tumor Suppressor :: down
HLA-A :: Tumor Suppressor :: down
RUNX1 :: Tumor Suppressor :: down
INPP4A :: Tumor Suppressor :: down
INPP4B :: Tumor Suppressor :: down
RRAGC :: Oncogene :: up
BTK :: Oncogene :: up
CCNQ :: Oncogene :: up
TP53 :: Tumor Suppressor :: down
EPHA3 :: Oncogene :: up
RTEL1 :: Tumor Suppressor :: down
EPAS1 :: Oncogene :: up
DCUN1D1 :: Oncogene :: up
PIK3R3 :: Oncogene :: up
PIK3R2 :: Oncogene :: up
MST1R :: Oncogene :: up
PIK3R1 :: Oncogene :: up
CD79B :: Oncogene :: up
CD79A :: Oncogene :: up
BRIP1 :: Tumor Suppressor :: down
RRAS :: Oncogene :: up
PGBD5 :: Oncogene :: up
H3C3 :: Tumor Suppressor :: down
TP53BP1 :: Tumor Suppressor :: down
H3C2 :: Tumor Suppressor :: down
H3C4 :: Tumor Suppressor :: down
RBM10 :: Tumor Suppressor :: down
H3C7 :: Tumor Suppressor :: down
H3C6 :: Tumor Suppressor :: down
STAT5A :: Oncogene :: up
ZRSR2 :: Tumor Suppressor :: down
STAT5B :: Oncogene :: up
WWTR1 :: Oncogene :: up
YES1 :: Oncogene :: up
SETDB1 :: Oncogene :: up
XRCC2 :: Tumor Suppressor :: down
INSR :: Oncogene :: up
SH2D1A :: Oncogene :: up
IGF2 :: Oncogene :: up
IGF1 :: Oncogene :: up
SMARCA2 :: Tumor Suppressor :: down
SMARCA4 :: Tumor Suppressor :: down
STAG2 :: Tumor Suppressor :: down
FUBP1 :: Tumor Suppressor :: down
ATM :: Tumor Suppressor :: down
CALR :: Oncogene :: up
BAP1 :: Tumor Suppressor :: down
ATR :: Tumor Suppressor :: down
PTPRT :: Tumor Suppressor :: down
PTPRS :: Tumor Suppressor :: down
BRCA1 :: Tumor Suppressor :: down
BRCA2 :: Tumor Suppressor :: down
BABAM1 :: Tumor Suppressor :: down
RPTOR :: Oncogene :: up
XPO1 :: Oncogene :: up
RAC2 :: Oncogene :: up
RAC1 :: Oncogene :: up
H3-3A :: Tumor Suppressor :: down
IL10 :: Tumor Suppressor :: down
H3C8 :: Tumor Suppressor :: down
PBRM1 :: Tumor Suppressor :: down
PARP1 :: Tumor Suppressor :: down
SYK :: Oncogene :: up
NCOA3 :: Oncogene :: up
MST1 :: Tumor Suppressor :: down
PDCD1LG2 :: Tumor Suppressor :: down
RHOA :: Oncogene :: up
RAD51B :: Tumor Suppressor :: down
RAD51D :: Tumor Suppressor :: down
RAD51C :: Tumor Suppressor :: down
CSDE1 :: Tumor Suppressor :: down
KIT :: Oncogene :: up
STK40 :: Oncogene :: up
DDR2 :: Oncogene :: up
YAP1 :: Oncogene :: up
AMER1 :: Tumor Suppressor :: down
PRKN :: Tumor Suppressor :: down
DOT1L :: Oncogene :: up
XIAP :: Oncogene :: up
CXCR4 :: Oncogene :: up
TMPRSS2 :: Oncogene :: up
ALOX12B :: Oncogene :: up
PAK1 :: Oncogene :: up
RXRA :: Oncogene :: up
SLX4 :: Tumor Suppressor :: down
RAD54L :: Tumor Suppressor :: down
SHOC2 :: Oncogene :: up
PAK5 :: Oncogene :: up
SUZ12 :: Oncogene :: up
NPM1 :: Oncogene :: up
MAP3K1 :: Tumor Suppressor :: down
H2BC5 :: Tumor Suppressor :: down
MLH1 :: Tumor Suppressor :: down
VEGFA :: Oncogene :: up
ETAA1 :: Tumor Suppressor :: down
RIT1 :: Oncogene :: up
AXL :: Oncogene :: up
CTNNB1 :: Oncogene :: up
TRIP13 :: Oncogene :: up
FOXA1 :: Oncogene :: up
MPL :: Oncogene :: up
INPPL1 :: Tumor Suppressor :: down
PRDM1 :: Tumor Suppressor :: down
ARHGAP35 :: Tumor Suppressor :: down
IGF1R :: Oncogene :: up
CCND3 :: Oncogene :: up
CCND2 :: Oncogene :: up
CCND1 :: Oncogene :: up
EP300 :: Tumor Suppressor :: down
ARID2 :: Tumor Suppressor :: down
PDGFRB :: Oncogene :: up
LMO1 :: Oncogene :: up
PDGFRA :: Oncogene :: up
HGF :: Oncogene :: up
TSC2 :: Tumor Suppressor :: down
ARID5B :: Tumor Suppressor :: down
TSC1 :: Tumor Suppressor :: down
SDHC :: Tumor Suppressor :: down
SDHD :: Tumor Suppressor :: down
SDHA :: Tumor Suppressor :: down
MYCL :: Oncogene :: up
MYCN :: Oncogene :: up
SLFN11 :: Tumor Suppressor :: down
CCNE1 :: Oncogene :: up
RAF1 :: Oncogene :: up
CARD11 :: Oncogene :: up
HOXB13 :: Oncogene :: up
COP1 :: Tumor Suppressor :: down
TMEM127 :: Tumor Suppressor :: down
SMAD2 :: Tumor Suppressor :: down
SMAD4 :: Tumor Suppressor :: down
ZFHX3 :: Tumor Suppressor :: down
SMAD3 :: Tumor Suppressor :: down
IDH1 :: Oncogene :: up
PTCH1 :: Tumor Suppressor :: down
IDH2 :: Oncogene :: up
INHBA :: Oncogene :: up
ESR1 :: Oncogene :: up
PHOX2B :: Oncogene :: up
NFKBIA :: Tumor Suppressor :: down
FGF19 :: Oncogene :: up
GNB1 :: Oncogene :: up
GNAS :: Oncogene :: up
TCF3 :: Oncogene :: up
IL7R :: Oncogene :: up
FGFR4 :: Oncogene :: up
FGFR3 :: Oncogene :: up
FGFR2 :: Oncogene :: up
FGFR1 :: Oncogene :: up
BMPR1A :: Tumor Suppressor :: down
KDM5A :: Oncogene :: up
GSK3B :: Tumor Suppressor :: down
KDM5C :: Tumor Suppressor :: down
TNFAIP3 :: Tumor Suppressor :: down
FLCN :: Tumor Suppressor :: down
SPRED1 :: Tumor Suppressor :: down
CASP8 :: Tumor Suppressor :: down
POLE :: Tumor Suppressor :: down
KDM6A :: Tumor Suppressor :: down
EGFL7 :: Oncogene :: up
EED :: Tumor Suppressor :: down
PDPK1 :: Oncogene :: up
AXIN1 :: Tumor Suppressor :: down
ETV1 :: Oncogene :: up
AXIN2 :: Tumor Suppressor :: down
ARID1A :: Tumor Suppressor :: down
ARID1B :: Tumor Suppressor :: down
TENT5C :: Tumor Suppressor :: down
TGFBR1 :: Tumor Suppressor :: down
TGFBR2 :: Tumor Suppressor :: down
ETV6 :: Tumor Suppressor :: down
LATS1 :: Tumor Suppressor :: down
GREM1 :: Oncogene :: up
LATS2 :: Tumor Suppressor :: down
ELF3 :: Oncogene :: up
IRF4 :: Oncogene :: up
MYOD1 :: Oncogene :: up
RASA1 :: Tumor Suppressor :: down
ABRAXAS1 :: Tumor Suppressor :: down
CBL :: Tumor Suppressor :: down
AURKB :: Oncogene :: up
AURKA :: Oncogene :: up
ERBB3 :: Oncogene :: up
ERBB4 :: Oncogene :: up
POLD1 :: Tumor Suppressor :: down
GNA11 :: Oncogene :: up
ERBB2 :: Oncogene :: up
MAPK1 :: Oncogene :: up
DROSHA :: Oncogene :: up
VHL :: Tumor Suppressor :: down
MUTYH :: Tumor Suppressor :: down
MAPK3 :: Oncogene :: up
SPEN :: Tumor Suppressor :: down
TCF7L2 :: Oncogene :: up
NEGR1 :: Tumor Suppressor :: down
TSHR :: Oncogene :: up
H3-5 :: Oncogene :: up
REST :: Tumor Suppressor :: down
H3-4 :: Oncogene :: up
ERCC3 :: Tumor Suppressor :: down
ERCC4 :: Tumor Suppressor :: down
CARM1 :: Oncogene :: up
ERCC2 :: Tumor Suppressor :: down
RPS6KB2 :: Oncogene :: up
KRAS :: Oncogene :: up
ERCC5 :: Tumor Suppressor :: down
TEK :: Oncogene :: up
""",
}

# ─── Parsing ─────────────────────────────────────────────────────────────────
CANCER_TYPE = "Pancreatic (PDAC)"

# Map a source group to a coarse analyte type used for facet colouring / filtering.
def _analyte_type(source_group: str, category: str) -> str:
    c = category.lower()
    if "mirna" in c or source_group in ("Serum miRNA",):
        return "miRNA"
    if "lncrna" in c or source_group == "Serum lncRNA":
        return "lncRNA"
    if "exosom" in c or source_group == "Serum Liquid Biopsy":
        return "Liquid Biopsy"
    if "ctc" in c:
        return "CTC"
    if "ctdna" in c or "methylated dna" in c or c.startswith("dna"):
        return "ctDNA / DNA"
    if source_group in ("Structural Variant Gene", "Mutated Gene"):
        return "Gene"
    if "metallomics" in c or "polyamine" in c or "glucose" in c:
        return "Metabolite"
    if "antibody" in c:
        return "Antibody"
    if "rna" in c:
        return "RNA"
    return "Protein"


def _parse():
    rows = []
    seen = set()
    for group, block in _RAW.items():
        for line in block.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("::")]
            if len(parts) != 3:
                raise ValueError(f"Bad line in {group!r}: {line!r}")
            name, category, indication = parts
            key = (name, group)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "name": name,
                "category": category,
                "indication": indication,        # up | down | context | neutral
                "source_group": group,
                "analyte_type": _analyte_type(group, category),
            })
    return rows


BIOMARKERS = _parse()


def all_biomarker_names():
    """Unique biomarker names across all groups (sorted)."""
    return sorted({b["name"] for b in BIOMARKERS})


def source_groups():
    return list(_RAW.keys())


def by_group():
    out = {}
    for b in BIOMARKERS:
        out.setdefault(b["source_group"], []).append(b)
    return out


if __name__ == "__main__":
    from collections import Counter
    print(f"Total rows: {len(BIOMARKERS)}")
    print(f"Unique names: {len(all_biomarker_names())}")
    print("By group:")
    for g, n in Counter(b["source_group"] for b in BIOMARKERS).items():
        print(f"  {g:28s} {n}")
    print("By analyte type:")
    for t, n in Counter(b["analyte_type"] for b in BIOMARKERS).items():
        print(f"  {t:16s} {n}")
