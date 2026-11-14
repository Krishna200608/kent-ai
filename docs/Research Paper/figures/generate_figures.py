"""Generate publication-quality IEEE visual figures for the Kent-AI Research Paper."""

import matplotlib.pyplot as plt
import matplotlib.patches as patches

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9

def generate_system_architecture():
    fig, ax = plt.subplots(figsize=(15, 6.2), dpi=300)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 6.2)
    ax.axis('off')

    c_bg_stage = '#F4F7F9'
    c_navy = '#18324B'
    c_blue = '#286090'
    c_teal = '#1E8278'
    c_green = '#2E7D32'
    c_amber = '#C67A18'
    c_purple = '#5C4382'
    c_border = '#CCD6DD'
    c_box_bg = '#FFFFFF'

    fig.patch.set_facecolor('#FFFFFF')

    stages = [
        ('Stage 1: Conversational Intake', 0.2, 2.7, c_blue, [
            'Unstructured Patient Narrative',
            '10-State Dialogue Engine (FSM)',
            'Clickable Suggestion Palettes',
            'Dual Personas (Patient / Doctor)'
        ]),
        ('Stage 2: Sequence Labeling & QLoRA', 3.15, 3.1, c_teal, [
            'Multi-Encoder Taggers (768-d)',
            'BioLink, PubMed, ClinicalBERT',
            '4-bit QLoRA BioMistral 7B (NF4)',
            '15 BIO Classes (7 Kent Dimensions)'
        ]),
        ('Stage 3: 0-Drift Alignment & Ensemble', 6.5, 2.7, c_purple, [
            'Deterministic Offset Repair',
            '0% Coordinate Drift Snapping',
            'Spatial IoU Span Clustering',
            'Confidence-Weighted Soft Voting'
        ]),
        ('Stage 4: Dense Vector Search', 9.45, 2.7, c_amber, [
            'all-MiniLM-L6-v2 (384-dim)',
            'ChromaDB HNSW Cosine Index',
            '74,513 Kent Repertory Rubrics',
            'p99 Latency < 18 ms'
        ]),
        ('Stage 5: Totality Scoring & Workstation', 12.4, 2.4, c_green, [
            'Mathematical Totality Ranking',
            'Grade x Sim x IRF x Dim Weight',
            'Doctor-in-the-Loop Stepper',
            'Mute & Eliminatory Overrides'
        ]),
    ]

    for title, x, w, col, items in stages:
        rect = patches.FancyBboxPatch((x, 0.4), w, 5.2, boxstyle='Round,pad=0.1,rounding_size=0.18',
                                      facecolor=c_bg_stage, edgecolor=c_border, linewidth=1.2, zorder=1)
        ax.add_patch(rect)
        
        hdr = patches.FancyBboxPatch((x+0.05, 5.0), w-0.1, 0.5, boxstyle='Round,pad=0.08,rounding_size=0.12',
                                    facecolor=col, edgecolor='none', zorder=2)
        ax.add_patch(hdr)
        ax.text(x + w/2, 5.25, title, ha='center', va='center', color='#FFFFFF', fontweight='bold', fontsize=9.2, zorder=3)
        
        y_starts = [4.15, 3.1, 2.05, 1.0]
        for i, item_text in enumerate(items):
            item_box = patches.FancyBboxPatch((x+0.15, y_starts[i]-0.3), w-0.3, 0.75,
                                              boxstyle='Round,pad=0.06,rounding_size=0.1',
                                              facecolor=c_box_bg, edgecolor=col, linewidth=0.9, zorder=2)
            ax.add_patch(item_box)
            ax.text(x + w/2, y_starts[i]+0.07, item_text, ha='center', va='center', color=c_navy,
                    fontsize=8.0, fontweight='medium', zorder=3, multialignment='center')

    arrow_xs = [2.95, 6.3, 9.25, 12.2]
    for ax_x in arrow_xs:
        arrow = patches.FancyArrowPatch((ax_x, 3.0), (ax_x + 0.15, 3.0),
                                        arrowstyle='simple,head_width=9,head_length=8',
                                        facecolor=c_navy, edgecolor='none', zorder=4)
        ax.add_patch(arrow)

    banner = patches.FancyBboxPatch((0.2, 0.05), 14.6, 0.28, boxstyle='Square,pad=0.04',
                                    facecolor='#EAEFF4', edgecolor=c_border, linewidth=0.8, zorder=1)
    ax.add_patch(banner)
    ax.text(7.5, 0.19, r'TotalityScore(R) = $\sum_{r \in \mathcal{R}} \mathrm{Grade}(R,r) \cdot S(r) \cdot \ln(1 + N_{\mathrm{total}}/N_r) \cdot W(\mathrm{Dim}(r))$  |  19,732 Cases  |  0.00% Coordinate Drift  |  <10 Min Bedside Target',
            ha='center', va='center', color=c_navy, fontsize=8.2, fontweight='bold', zorder=3)

    plt.tight_layout()
    plt.savefig('docs/Research Paper/figures/fig1_system_architecture.png', dpi=300, bbox_inches='tight', pad_inches=0.05)
    plt.close()
    print('Generated fig1_system_architecture.png')


def generate_case_annotation_trace():
    fig, ax = plt.subplots(figsize=(12, 5.8), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5.8)
    ax.axis('off')
    fig.patch.set_facecolor('#FFFFFF')

    ax.text(6.0, 5.4, 'Representative Clinical Case-Taking Annotation & Subword Alignment Trace',
            ha='center', va='center', color='#18324B', fontsize=11, fontweight='bold')

    box_raw = patches.FancyBboxPatch((0.4, 4.0), 11.2, 0.9, boxstyle='Round,pad=0.08,rounding_size=0.12',
                                    facecolor='#F3F6F9', edgecolor='#B0BEC5', linewidth=1.2)
    ax.add_patch(box_raw)
    ax.text(0.6, 4.55, 'Raw Clinical Dialogue:', color='#286090', fontweight='bold', fontsize=9)
    raw_text = '"Doctor, every morning at 3 AM, I suffer from a throbbing pain in my left temple, relieved by cold wraps, with intense anxiety."'
    ax.text(0.6, 4.25, raw_text, color='#263238', fontsize=8.5, style='italic')

    box_alg = patches.FancyBboxPatch((0.4, 2.5), 11.2, 1.15, boxstyle='Round,pad=0.08,rounding_size=0.12',
                                    facecolor='#E8F5E9', edgecolor='#81C784', linewidth=1.2)
    ax.add_patch(box_alg)
    ax.text(0.6, 3.35, 'Deterministic Subword Alignment Algorithm (0% Coordinate Drift):', color='#2E7D32', fontweight='bold', fontsize=9)
    alg_details = (
        '• Step 1: Character Coordinate Verification [s, e] -> Local window check (+-15 char) -> Exact substring matching\n'
        '• Step 2: HuggingFace FastTokenizer offset_mapping intersection with entity intervals [s*, e*]\n'
        '• Step 3: Leading subword mapped to B-{Label}, continuation subwords mapped to I-{Label}, special tokens masked to -100'
    )
    ax.text(0.6, 2.8, alg_details, color='#1B5E20', fontsize=8.0)

    box_spans = patches.FancyBboxPatch((0.4, 0.3), 11.2, 1.85, boxstyle='Round,pad=0.08,rounding_size=0.12',
                                      facecolor='#F4F7F9', edgecolor='#90A4AE', linewidth=1.2)
    ax.add_patch(box_spans)
    ax.text(0.6, 1.85, 'Resolved 7-Dimension Kentian Clinical Entities & BIO Labels:', color='#18324B', fontweight='bold', fontsize=9)

    entities = [
        ('every morning at 3 AM', 'TEMP', 'B-TEMP / I-TEMP', '#E1BEE7', '#6A1B9A', 0.6, 1.25),
        ('throbbing pain', 'SEN', 'B-SEN / I-SEN', '#FFE0B2', '#E65100', 3.4, 1.25),
        ('left temple', 'LOC', 'B-LOC / I-LOC', '#C8E6C9', '#2E7D32', 5.9, 1.25),
        ('relieved by cold wraps', 'MOD_AMEL', 'B-MOD_AMEL / I-MOD_AMEL', '#B2EBF2', '#00838F', 8.2, 1.25),
        ('intense anxiety', 'MENT', 'B-MENT / I-MENT', '#FFCDD2', '#C62828', 0.6, 0.55),
        ('with nausea (concomitant)', 'CONC', 'B-CONC / I-CONC', '#D1C4E9', '#4527A0', 4.5, 0.55),
        ('Kent Evidential MIND Priority: W(MENT) = 3.0', 'RULE', 'Kentian Hierarchy Anchor', '#FFF9C4', '#F57F17', 8.2, 0.55),
    ]

    for txt, dim, bio, bg, fg, x, y in entities:
        span_box = patches.FancyBboxPatch((x, y-0.12), 2.5, 0.52, boxstyle='Round,pad=0.05,rounding_size=0.08',
                                          facecolor=bg, edgecolor=fg, linewidth=0.9)
        ax.add_patch(span_box)
        ax.text(x + 1.25, y + 0.2, f'[{dim}] {txt}', ha='center', va='center', color=fg, fontweight='bold', fontsize=7.2)
        ax.text(x + 1.25, y - 0.01, bio, ha='center', va='center', color='#37474F', fontsize=6.8)

    plt.tight_layout()
    plt.savefig('docs/Research Paper/figures/fig_case_annotation_trace.png', dpi=300, bbox_inches='tight', pad_inches=0.05)
    plt.close()
    print('Generated fig_case_annotation_trace.png')


def generate_two_stage_hybrid():
    fig, ax = plt.subplots(figsize=(12, 5.2), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5.2)
    ax.axis('off')
    fig.patch.set_facecolor('#FFFFFF')

    ax.text(6.0, 4.85, 'Two-Stage Hybrid Architecture: High-Throughput Encoders + LLM Contextual Arbitrator',
            ha='center', va='center', color='#18324B', fontsize=11, fontweight='bold')

    # Stage 1: Encoders
    box_s1 = patches.FancyBboxPatch((0.5, 0.8), 3.4, 3.6, boxstyle='Round,pad=0.1,rounding_size=0.15',
                                   facecolor='#EBF3FB', edgecolor='#286090', linewidth=1.2)
    ax.add_patch(box_s1)
    ax.text(2.2, 4.05, 'Stage 1: Encoder Candidate Mining', ha='center', va='center', color='#286090', fontweight='bold', fontsize=8.8)
    ax.text(2.2, 3.75, 'Sub-40 ms Execution Window', ha='center', va='center', color='#546E7A', fontsize=7.5, style='italic')

    models = [
        ('BioLinkBERT-Base (w=0.35)', 'Top BIO F1 (34.86%)', '#BBDEFB'),
        ('PubMedBERT (w=0.35)', 'Top Recall@20 (41.56%)', '#BBDEFB'),
        ('Bio_ClinicalBERT (w=0.20)', 'ICU Modalities Lead', '#E3F2FD'),
        ('DeBERTa-v3 (w=0.10)', 'Holistic Embedding Prior', '#E3F2FD'),
    ]
    y_m = [3.2, 2.5, 1.8, 1.1]
    for i, (m_name, m_sub, bg) in enumerate(models):
        m_box = patches.FancyBboxPatch((0.7, y_m[i]-0.25), 3.0, 0.55, boxstyle='Round,pad=0.05,rounding_size=0.08',
                                       facecolor=bg, edgecolor='#1E88E5', linewidth=0.8)
        ax.add_patch(m_box)
        ax.text(2.2, y_m[i]+0.06, m_name, ha='center', va='center', color='#0D47A1', fontweight='bold', fontsize=7.5)
        ax.text(2.2, y_m[i]-0.12, m_sub, ha='center', va='center', color='#37474F', fontsize=6.8)

    # Arrow to Clustering
    arr1 = patches.FancyArrowPatch((3.95, 2.6), (4.45, 2.6), arrowstyle='simple,head_width=8,head_length=8',
                                   facecolor='#18324B', edgecolor='none')
    ax.add_patch(arr1)

    # Clustering Box
    box_clu = patches.FancyBboxPatch((4.5, 1.4), 2.8, 2.4, boxstyle='Round,pad=0.1,rounding_size=0.15',
                                    facecolor='#F3E5F5', edgecolor='#8E24AA', linewidth=1.2)
    ax.add_patch(box_clu)
    ax.text(5.9, 3.45, 'Spatial IoU Span Clustering', ha='center', va='center', color='#6A1B9A', fontweight='bold', fontsize=8.5)
    clu_text = (
        '• Overlap: IoU(A, B) >= 0.40\n'
        '• Weighted Confidence:\n'
        '  C(K) = sum(w_m) >= 0.20\n'
        '• Widest span selected\n'
        '• Mined Candidate Pool'
    )
    ax.text(4.7, 2.3, clu_text, color='#4A148C', fontsize=7.5)

    # Arrow to Stage 2
    arr2 = patches.FancyArrowPatch((7.35, 2.6), (7.85, 2.6), arrowstyle='simple,head_width=8,head_length=8',
                                   facecolor='#18324B', edgecolor='none')
    ax.add_patch(arr2)

    # Stage 2: LLM Arbitration
    box_s2 = patches.FancyBboxPatch((7.9, 0.8), 3.6, 3.6, boxstyle='Round,pad=0.1,rounding_size=0.15',
                                   facecolor='#E8F5E9', edgecolor='#2E7D32', linewidth=1.2)
    ax.add_patch(box_s2)
    ax.text(9.7, 4.05, 'Stage 2: Generative Arbitration', ha='center', va='center', color='#1B5E20', fontweight='bold', fontsize=8.8)
    ax.text(9.7, 3.75, 'BioMistral 7B (4-bit QLoRA, NF4)', ha='center', va='center', color='#388E3C', fontsize=7.5, fontweight='bold')

    s2_items = [
        ('Boundary Arbitration', 'Resolves span overlap conflicts'),
        ('Negation Detection', 'Filters "no nausea", "denies anxiety"'),
        ('Strict JSON Conformance', '100% Schema Validity (0 faults)'),
        ('Hallucination Filter', '99.73% Grounded (0.27% rate)'),
    ]
    y_s2 = [3.2, 2.5, 1.8, 1.1]
    for i, (title_s, sub_s) in enumerate(s2_items):
        item_box = patches.FancyBboxPatch((8.1, y_s2[i]-0.25), 3.2, 0.55, boxstyle='Round,pad=0.05,rounding_size=0.08',
                                         facecolor='#FFFFFF', edgecolor='#4CAF50', linewidth=0.8)
        ax.add_patch(item_box)
        ax.text(9.7, y_s2[i]+0.06, title_s, ha='center', va='center', color='#1B5E20', fontweight='bold', fontsize=7.5)
        ax.text(9.7, y_s2[i]-0.12, sub_s, ha='center', va='center', color='#37474F', fontsize=6.8)

    plt.tight_layout()
    plt.savefig('docs/Research Paper/figures/fig_two_stage_hybrid.png', dpi=300, bbox_inches='tight', pad_inches=0.05)
    plt.close()
    print('Generated fig_two_stage_hybrid.png')


def generate_clinical_workflow():
    fig, ax = plt.subplots(figsize=(14, 5.0), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5.0)
    ax.axis('off')
    fig.patch.set_facecolor('#FFFFFF')

    ax.text(7.0, 4.65, 'Doctor-in-the-Loop Clinical Workstation Workflow & Latency Compression',
            ha='center', va='center', color='#18324B', fontsize=11, fontweight='bold')

    steps = [
        ('Step 1: Intake', 'Conversational Intake\n• 10-state FSM dialog\n• Dynamic prompt chips\n• Patient/Dr. personas', '#E3F2FD', '#1976D2', 0.4),
        ('Step 2: Review', 'Symptom Verification\n• Span inspection\n• Real-time edit/delete\n• Dimension validation', '#EDE7F6', '#673AB7', 3.8),
        ('Step 3: Analysis', 'Totality Matrix\n• Mute & Eliminatory\n• Evidential grades\n• Simillimum ranking', '#E8F5E9', '#388E3C', 7.2),
        ('Step 4: Report', 'Clinical Documentation\n• Authenticated PDF\n• Provenance rubrics\n• Remedy differentials', '#FFF3E0', '#F57C00', 10.6),
    ]

    for title, desc, bg, fg, x in steps:
        box = patches.FancyBboxPatch((x, 1.2), 3.0, 2.9, boxstyle='Round,pad=0.1,rounding_size=0.14',
                                     facecolor=bg, edgecolor=fg, linewidth=1.3)
        ax.add_patch(box)
        hdr = patches.FancyBboxPatch((x+0.1, 3.4), 2.8, 0.55, boxstyle='Round,pad=0.06,rounding_size=0.1',
                                     facecolor=fg, edgecolor='none')
        ax.add_patch(hdr)
        ax.text(x+1.5, 3.68, title, ha='center', va='center', color='#FFFFFF', fontweight='bold', fontsize=9.2)
        ax.text(x+1.5, 2.3, desc, ha='center', va='center', color='#263238', fontsize=8.0)

    for arrow_x in [3.45, 6.85, 10.25]:
        arr = patches.FancyArrowPatch((arrow_x, 2.6), (arrow_x+0.3, 2.6), arrowstyle='simple,head_width=8,head_length=8',
                                      facecolor='#18324B', edgecolor='none')
        ax.add_patch(arr)

    # Time compression comparison bar
    bar_box = patches.FancyBboxPatch((0.4, 0.15), 13.2, 0.75, boxstyle='Round,pad=0.06,rounding_size=0.1',
                                     facecolor='#F4F7F9', edgecolor='#B0BEC5', linewidth=1.0)
    ax.add_patch(bar_box)
    ax.text(3.5, 0.52, 'Conventional Manual Workflow: 40 - 60 Minutes per Patient',
            ha='center', va='center', color='#C62828', fontweight='bold', fontsize=8.5)
    ax.text(10.5, 0.52, 'Kent-AI Augmented Workflow: < 10 Minutes per Patient (4x-6x Acceleration)',
            ha='center', va='center', color='#2E7D32', fontweight='bold', fontsize=8.5)

    plt.tight_layout()
    plt.savefig('docs/Research Paper/figures/fig_clinical_workflow.png', dpi=300, bbox_inches='tight', pad_inches=0.05)
    plt.close()
    print('Generated fig_clinical_workflow.png')


if __name__ == '__main__':
    generate_system_architecture()
    generate_case_annotation_trace()
    generate_two_stage_hybrid()
    generate_clinical_workflow()
    print('ALL FIGURES GENERATED SUCCESSFULLY!')
