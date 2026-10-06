"""Build docs/outbreak-synth-plan.pdf, the plain-language plan for Outbreak Synth (OS)."""
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

F = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("Sans", F + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", F + "DejaVuSans-Bold.ttf"))
registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans", boldItalic="Sans-Bold")

INK, MUTED, ACCENT, SOFT, LINE = (colors.HexColor(c) for c in ("#1f2328", "#57606a", "#0b6e4f", "#eef6f2", "#d0d7de"))

s_title = ParagraphStyle("t", fontName="Sans-Bold", fontSize=20, leading=24, textColor=INK, spaceAfter=4)
s_sub = ParagraphStyle("s", fontName="Sans", fontSize=10, leading=14, textColor=MUTED, spaceAfter=14)
s_h = ParagraphStyle("h", fontName="Sans-Bold", fontSize=13, leading=17, textColor=ACCENT, spaceBefore=12, spaceAfter=5)
s_body = ParagraphStyle("b", fontName="Sans", fontSize=9.5, leading=13.5, textColor=INK, spaceAfter=5, alignment=TA_LEFT)
s_bul = ParagraphStyle("u", parent=s_body, leftIndent=12, bulletIndent=2, spaceAfter=3)
s_cell = ParagraphStyle("c", fontName="Sans", fontSize=8.6, leading=11.5, textColor=INK)
s_cellb = ParagraphStyle("cb", parent=s_cell, fontName="Sans-Bold")
s_note = ParagraphStyle("n", parent=s_body, fontSize=8.5, leading=12, textColor=MUTED)

P = lambda t, s=s_body: Paragraph(t, s)
B = lambda t: Paragraph(t, s_bul, bulletText="•")


def table(rows, widths, header=True):
    data = [[Paragraph(c, s_cellb if (header and i == 0) else s_cell) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign="LEFT")
    st = [("GRID", (0, 0), (-1, -1), 0.5, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if header:
        st.append(("BACKGROUND", (0, 0), (-1, 0), SOFT))
    t.setStyle(TableStyle(st))
    return t


def flow():
    """Daily loop: fob rows -> Kinship Vote -> Two-Part Recipe -> Fresh-Days Check -> Green Light -> Synth."""
    w, h = 7.0 * inch, 2.0 * inch
    d = Drawing(w, h)
    boxes = [("fob's rows", "so far"), ("Kinship", "Vote"), ("Two-Part", "Recipe"), ("Fresh-Days", "Check"),
             ("Green", "Light?"), ("Synth", "Release")]
    bw, bh, gap, y = 0.95 * inch, 0.62 * inch, 0.24 * inch, 0.85 * inch
    xs = [i * (bw + gap) for i in range(len(boxes))]
    for i, (a, b) in enumerate(boxes):
        fill = SOFT if i in (1, 2, 3, 4) else colors.white
        d.add(Rect(xs[i], y, bw, bh, rx=6, ry=6, fillColor=fill, strokeColor=ACCENT, strokeWidth=1))
        d.add(String(xs[i] + bw / 2, y + bh / 2 + 3, a, fontName="Sans-Bold", fontSize=8.5, textAnchor="middle", fillColor=INK))
        d.add(String(xs[i] + bw / 2, y + bh / 2 - 9, b, fontName="Sans", fontSize=8.5, textAnchor="middle", fillColor=INK))
        if i:
            x0, x1, ym = xs[i - 1] + bw, xs[i], y + bh / 2
            d.add(Line(x0 + 2, ym, x1 - 4, ym, strokeColor=MUTED, strokeWidth=1))
            d.add(Polygon([x1 - 2, ym, x1 - 8, ym + 3.5, x1 - 8, ym - 3.5], fillColor=MUTED, strokeColor=MUTED))
    # Outbreak Atlas feeding the Kinship Vote
    ax = xs[1]
    d.add(Rect(ax, 0.05 * inch, bw * 2 + gap, 0.42 * inch, rx=6, ry=6, fillColor=colors.white, strokeColor=MUTED, strokeDashArray=[3, 2]))
    d.add(String(ax + (bw * 2 + gap) / 2, 0.21 * inch, "Outbreak Atlas (past outbreaks)", fontName="Sans", fontSize=8.5, textAnchor="middle", fillColor=MUTED))
    d.add(Line(ax + bw / 2, 0.47 * inch, ax + bw / 2, y - 3, strokeColor=MUTED))
    d.add(Polygon([ax + bw / 2, y - 1, ax + bw / 2 - 3.5, y - 7, ax + bw / 2 + 3.5, y - 7], fillColor=MUTED, strokeColor=MUTED))
    # "not yet" loop back from Green Light to fob's rows (tomorrow)
    gx = xs[4] + bw / 2
    top = y + bh + 0.26 * inch
    d.add(Line(gx, y + bh, gx, top, strokeColor=MUTED))
    d.add(Line(gx, top, xs[0] + bw / 2, top, strokeColor=MUTED))
    d.add(Line(xs[0] + bw / 2, top, xs[0] + bw / 2, y + bh + 4, strokeColor=MUTED))
    d.add(Polygon([xs[0] + bw / 2, y + bh + 1, xs[0] + bw / 2 - 3.5, y + bh + 7, xs[0] + bw / 2 + 3.5, y + bh + 7], fillColor=MUTED, strokeColor=MUTED))
    d.add(String((gx + xs[0] + bw / 2) / 2, top + 4, "not yet → wait for tomorrow's rows", fontName="Sans", fontSize=8, textAnchor="middle", fillColor=MUTED))
    return d


def footer(c, doc):
    c.saveState()
    c.setFont("Sans", 7.5)
    c.setFillColor(MUTED)
    c.drawString(0.75 * inch, 0.5 * inch, "Outbreak Synth (OS) · plan · 2026-10-06")
    c.drawRightString(7.75 * inch, 0.5 * inch, f"Page {doc.page}")
    c.restoreState()


story = [
    P("Outbreak Synth (OS)", s_title),
    P("What we are building, in plain words: a learner that studies past outbreaks, follows a new one day by day, "
      "says when it understands it, and only then generates synthetic patient data.", s_sub),

    P("1. The problem", s_h),
    P("When a new disease (we call it <b>fob</b>, a future outbreak) appears, scientists have only a few rows of "
      "patient records. Years later there are millions, but by then it is too late to help. OS asks: on day 20, "
      "can we understand fob well enough to generate millions of realistic patient rows, by combining fob's first "
      "rows with what we learned from every earlier outbreak?"),
    P("<b>How we score understanding:</b> each day, OS's model of fob predicts which hospitalised patients die, and "
      "is tested on fob patients from <i>later</i> dates (AUC). The <b>gold standard</b> is a model trained on all "
      "the data we have today. The <b>plateau day</b> is the first day OS comes within 0.02 of the gold standard."),

    P("2. The parts of OS", s_h),
    table([
        ["Name", "What it does", "Question it answers"],
        ["<b>Outbreak Atlas</b>", "The library of past outbreaks, all mapped to the same fields (age, sex, race, state, "
         "6 symptoms, 10 existing conditions, outcome). Today: 24 Brazilian outbreaks, about 2.15 million patients.",
         "What have we seen before?"],
        ["<b>Kinship Vote</b>", "Every past outbreak's model tries to predict fob's actual patients. The better it "
         "predicts them, the more votes it gets. Votes are shares that add to 100%, e.g. 55% flu-2016, 30% H1N1, 15% Stranger.",
         "Which past outbreaks is fob related to, and how sure are we?"],
        ["<b>Stranger Flag</b>", "A 'none of the above' candidate that assumes nothing from the past. If it wins the "
         "Kinship Vote, fob is flagged as new and OS stops borrowing.", "Is fob unlike anything we have seen?"],
        ["<b>Two-Part Recipe</b>", "OS's model of fob: a <b>Profile Model</b> (who ends up in hospital) and a "
         "<b>Severity Model</b> (who dies, given their profile).", "What does fob look like, and who does it kill?"],
        ["<b>Handover Rule</b>", "fob's overall deadliness is always learned from fob's own rows. How much each risk factor "
         "matters is borrowed from its kin at first, then handed over to fob's own data as rows arrive. The handover "
         "speed is learned from past outbreaks.", "What should we borrow, and for how long?"],
        ["<b>Fresh-Days Check</b>", "Every day, each candidate recipe trains on fob's data up to 3 days ago and is scored "
         "on fob's 3 newest days. A recipe that looked right by kinship but fails here loses.", "Is the borrowed knowledge actually working on fob?"],
        ["<b>Green Light</b>", "The readiness signal. It turns green when the Fresh-Days score has been stable, the main risk "
         "factors are pinned down, and past outbreaks plateaued at a similar point. Until then OS says 'not yet'.",
         "Do we understand fob well enough to generate?"],
        ["<b>Synth Release</b>", "Only after the Green Light: draw as many synthetic rows as needed from the Two-Part "
         "Recipe, then compare them side by side with fob's real rows before anyone uses them.", "Give scientists the data."],
        ["<b>Glass Box Report</b>", "A daily readable report: the Kinship Vote and why, a risk table (past effect vs fob's "
         "effect, with uncertainty), and why the light is green or not. A doctor can read it and veto it.",
         "Why did OS decide this?"],
        ["<b>OC (Outbreak Comprehension)</b>", "The whole learning step: Kinship Vote + Two-Part Recipe + Handover Rule + "
         "Fresh-Days Check. OC is what improves day by day.", "How well does OS understand fob today?"],
    ], [1.3 * inch, 3.9 * inch, 1.8 * inch]),

    Spacer(1, 10),
    KeepTogether([P("3. One day in the life of OS", s_h), Spacer(1, 4), flow(),
                  P("Every day new fob rows arrive. OS re-runs the Kinship Vote, updates the Two-Part Recipe with the "
                    "Handover Rule, scores it with the Fresh-Days Check, and decides on the Green Light. 'Not yet' means "
                    "wait for tomorrow's rows.", s_note)]),

    P("4. Example: the 5-groups question", s_h),
    P("Suppose the Atlas holds groups A–E and fob arrives. OS never labels fob 'group B' by hand. On day 3, with 20 rows, "
      "the Kinship Vote might be 30% B, 25% A, 20% Stranger and the rest spread out: OS is honestly unsure, so it borrows "
      "little. By day 15 it might be 80% B, because B's past outbreaks keep predicting fob's real patients best. Inside B, "
      "the Fresh-Days Check decides between the recipes that worked for B1, B2 and so on: they compete on fob's own newest "
      "days, and the best one wins."),

    P("5. Why trust it? The Time Machine Replay", s_h),
    P("We pretend each past outbreak is fob, hide everything after it, and replay it day by day. That gives four checks:"),
    B("<b>Right kin?</b> Did the Kinship Vote point to the outbreaks that, in hindsight, were most similar? "
      "Sanity checks: a flu season should pick other flu seasons, and RSV (mostly babies) should pick RSV."),
    B("<b>Honest confidence?</b> When OS says '80% B', it should be right about 80% of the time."),
    B("<b>Earlier plateau?</b> OS must reach the plateau sooner than real data alone, and beat 'borrow everything' "
      "and 'borrow nothing'. We report the <b>worst</b> outbreak, not just the average."),
    B("<b>Honest Green Light?</b> Whenever the light was green, OS really was within 0.02 of the gold standard."),

    P("6. What we already know (real Brazilian data, SIVEP-Gripe, CC-BY)", s_h),
    table([
        ["Finding", "Number"],
        ["Real data alone: plateau day for COVID-19 (2020)", "day 33 (2,824 patients)"],
        ["Real data alone: plateau day for H1N1 (2009)", "day 56 (7,315 patients)"],
        ["Days with too little data to train at all", "COVID days 0–20, H1N1 days 0–26"],
        ["Model trained only on pre-2020 outbreaks, scored on COVID", "AUC 0.727, but age alone also gives 0.727"],
        ["Death rate: past outbreaks vs COVID", "11.5% vs 33.6%"],
    ], [4.6 * inch, 2.4 * inch]),
    Spacer(1, 4),
    P("This is why OS is designed this way. Borrowing everything from the past taught OS only 'older patients die more'. "
      "And copying the past's death rate would have shown a third of COVID's real deaths. So the Kinship Vote chooses whom "
      "to borrow from, and the Handover Rule never borrows deadliness."),

    P("7. Build order", s_h),
    table([
        ["Step", "What", "Done when"],
        ["1", "Kinship Vote + Stranger Flag", "The Time Machine Replay over all 24 outbreaks picks sensible kin"],
        ["2", "Two-Part Recipe + Handover Rule", "COVID 2020 replay reaches the plateau before day 33"],
        ["3", "Fresh-Days Check + Green Light", "The Green Light is honest in every replay"],
        ["4", "Synth Release + Glass Box Report", "Synthetic rows match fob's real rows on the side-by-side check"],
        ["5", "More outbreaks (mpox, Ebola, SARS, MERS, other countries)", "OS is tested on diseases unlike Brazil's respiratory ones"],
    ], [0.5 * inch, 3.0 * inch, 3.5 * inch]),

    P("8. Limits we say up front", s_h),
    B("Synthetic rows hold no more information than fob's real rows plus what OS learned from past outbreaks. "
      "Ten million rows is a format, not new knowledge. The Stranger Flag and the Green Light keep OS honest about this."),
    B("This data covers who gets severely ill and who dies. It cannot show vaccine side effects, and synthetic data cannot "
      "replace clinical trials. Early on, OS can help decide who is at high risk, whom to protect first and whom to include in a trial."),
    B("The Atlas has 24 outbreaks but only about 4 truly different diseases. That is the real sample size behind any "
      "claim of trust. Adding more diseases is part of the plan, not an extra."),
    B("Some things make outbreaks look alike for the wrong reasons: form changes (the 2019+ form leaves far more fields "
      "blank), unusual first patients, and changes in testing. The Kinship Vote has to correct for them, and the replays check that it did."),
]

doc = SimpleDocTemplate("docs/outbreak-synth-plan.pdf", pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                        topMargin=0.7 * inch, bottomMargin=0.8 * inch, title="Outbreak Synth (OS): plan",
                        author="outbreak-synth project")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("wrote docs/outbreak-synth-plan.pdf")
