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
s_h = ParagraphStyle("h", fontName="Sans-Bold", fontSize=13, leading=17, textColor=ACCENT, spaceBefore=10, spaceAfter=4)
s_body = ParagraphStyle("b", fontName="Sans", fontSize=9.3, leading=12.8, textColor=INK, spaceAfter=5, alignment=TA_LEFT)
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
    boxes = [("fob's data", "so far"), ("Kinship", "Vote"), ("Two-Part", "Recipe"), ("Fresh-Days", "Check"),
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
    d.add(Rect(ax, 0.05 * inch, bw * 3 + gap * 2, 0.42 * inch, rx=6, ry=6, fillColor=colors.white, strokeColor=MUTED, strokeDashArray=[3, 2]))
    d.add(String(ax + (bw * 3 + gap * 2) / 2, 0.21 * inch, "Atlas (past outbreaks or past vaccines)", fontName="Sans", fontSize=8.5, textAnchor="middle", fillColor=MUTED))
    d.add(Line(ax + bw / 2, 0.47 * inch, ax + bw / 2, y - 3, strokeColor=MUTED))
    d.add(Polygon([ax + bw / 2, y - 1, ax + bw / 2 - 3.5, y - 7, ax + bw / 2 + 3.5, y - 7], fillColor=MUTED, strokeColor=MUTED))
    # "not yet" loop back from Green Light to fob's rows (tomorrow)
    gx = xs[4] + bw / 2
    top = y + bh + 0.26 * inch
    d.add(Line(gx, y + bh, gx, top, strokeColor=MUTED))
    d.add(Line(gx, top, xs[0] + bw / 2, top, strokeColor=MUTED))
    d.add(Line(xs[0] + bw / 2, top, xs[0] + bw / 2, y + bh + 4, strokeColor=MUTED))
    d.add(Polygon([xs[0] + bw / 2, y + bh + 1, xs[0] + bw / 2 - 3.5, y + bh + 7, xs[0] + bw / 2 + 3.5, y + bh + 7], fillColor=MUTED, strokeColor=MUTED))
    d.add(String((gx + xs[0] + bw / 2) / 2, top + 4, "not yet → wait for more data", fontName="Sans", fontSize=8, textAnchor="middle", fillColor=MUTED))
    return d


def footer(c, doc):
    c.saveState()
    c.setFont("Sans", 7.5)
    c.setFillColor(MUTED)
    c.drawString(0.75 * inch, 0.5 * inch, "Outbreak Synth (OS) · plan v2 · 2026-10-06")
    c.drawRightString(7.75 * inch, 0.5 * inch, f"Page {doc.page}")
    c.restoreState()


story = [
    P("Outbreak Synth (OS)", s_title),
    P("One general method, two case studies. OS studies the past, follows something new day by day, says when it "
      "understands it, and only then generates synthetic data. Case Study 1: a new disease outbreak. "
      "Case Study 2: side-effect signals from a new vaccine.", s_sub),

    P("1. The idea", s_h),
    P("Something new appears, which we call <b>fob</b>. In Case Study 1, fob is a new disease; in Case Study 2, it is a "
      "new vaccine being rolled out. At first there are only a few records. Years later there are millions, but by then "
      "it is too late to help. OS asks: <b>can we understand fob early</b>, by combining its first records with "
      "everything learned from similar things in the past, and <b>know when that understanding is good enough</b> to "
      "act on and to generate data from?"),
    P("The contribution is the <b>method</b>: choosing what to learn from (Kinship Vote), what to borrow and for how "
      "long (Handover Rule), checking itself on fresh data (Fresh-Days Check), deciding when it is ready (Green Light), "
      "and explaining every decision (Glass Box Report). Two different case studies show it works beyond one setting."),
    table([
        ["", "Case Study 1: early outbreak", "Case Study 2: vaccine side-effect signals"],
        ["<b>fob</b>", "A new disease", "A new vaccine being rolled out"],
        ["<b>Time step</b>", "Days since the first patient record", "Weeks since rollout began"],
        ["<b>Atlas</b>", "Outbreak Atlas: past outbreaks", "Vaccine Atlas: past vaccines and their known side effects"],
        ["<b>Kin</b>", "Outbreaks with similar patients and severity",
         "Vaccines of the same type (mRNA, viral vector, inactivated) or used in the same age groups"],
        ["<b>What OS learns</b>", "Who is hospitalised and who dies", "Which side effects occur more often than expected, and in whom"],
        ["<b>Score</b>", "AUC on later patients; the day OS reaches the plateau",
         "Weeks until a real signal is caught; number of false alarms"],
        ["<b>Green Light means</b>", "'I understand this disease well enough to generate data'",
         "'This signal is real' (or 'no signal yet')"],
        ["<b>Data status</b>", "Done: Brazil SIVEP-Gripe, CC-BY, 24 outbreaks", "To check: public reporting systems (see section 7)"],
    ], [1.25 * inch, 2.75 * inch, 3.0 * inch]),

    P("2. The parts of OS (shared by both case studies)", s_h),
    table([
        ["Name", "What it does", "Question it answers"],
        ["<b>Atlas</b>", "The library of the past, mapped to the same fields. Case Study 1: the <b>Outbreak Atlas</b> "
         "(24 Brazilian outbreaks, about 2.15 million patients). Case Study 2: the <b>Vaccine Atlas</b>.",
         "What have we seen before?"],
        ["<b>Kinship Vote</b>", "Every past entry's model tries to predict fob's actual records. The better it predicts them, "
         "the more votes it gets. Votes are shares that add to 100%, e.g. 55% flu-2016, 30% H1N1, 15% Stranger.",
         "What is fob related to, and how sure are we?"],
        ["<b>Stranger Flag</b>", "A 'none of the above' candidate that assumes nothing from the past. If it wins the "
         "Kinship Vote, fob is flagged as new and OS stops borrowing.", "Is fob unlike anything we have seen?"],
        ["<b>Two-Part Recipe</b>", "OS's model of fob. A <b>Profile Model</b> describes who is affected; a <b>Severity "
         "Model</b> describes what happens to them (death in Case Study 1; side effect in Case Study 2).",
         "What does fob look like, and what does it do?"],
        ["<b>Handover Rule</b>", "fob's overall rate (how deadly it is, or how often a side effect occurs) is always learned "
         "from fob's own data. How much each risk factor matters is borrowed from kin at first, then handed over to fob's own "
         "data as it grows. The handover speed is learned from the past.", "What should we borrow, and for how long?"],
        ["<b>Fresh-Days Check</b>", "Each candidate recipe trains on fob's data up to a few days (or weeks) ago and is scored "
         "on the newest data. A recipe that looked right by kinship but fails here loses.", "Is the borrowed knowledge working on fob?"],
        ["<b>Green Light</b>", "The readiness signal. It turns green when the Fresh-Days score is stable, the key quantities "
         "are pinned down, and similar past cases were ready at a similar point. Until then OS says 'not yet'.",
         "Is OS ready to act or generate?"],
        ["<b>Synth Release</b>", "Only after the Green Light: draw synthetic rows from the Two-Part Recipe, check them side "
         "by side with fob's real data, and label every file as synthetic.", "Give scientists usable data."],
        ["<b>Glass Box Report</b>", "A readable daily report: the Kinship Vote and why, a risk table (past effect vs fob's "
         "effect, with uncertainty), and why the light is green or not. An expert can read it and veto it.",
         "Why did OS decide this?"],
        ["<b>OC (Outbreak Comprehension)</b>", "The whole learning step: Kinship Vote + Two-Part Recipe + Handover Rule + "
         "Fresh-Days Check. OC is what improves as data arrives.", "How well does OS understand fob today?"],
    ], [1.3 * inch, 3.9 * inch, 1.8 * inch]),

    Spacer(1, 4),
    KeepTogether([P("3. One step in the life of OS", s_h), Spacer(1, 4), flow(),
                  P("Each day (or week), new fob data arrives. OS re-runs the Kinship Vote, updates the Two-Part Recipe "
                    "with the Handover Rule, scores it with the Fresh-Days Check, and decides on the Green Light. "
                    "'Not yet' means wait for more data.", s_note)]),

    P("4. Example: the 5-groups question", s_h),
    P("Suppose the Atlas holds groups A–E and fob arrives. OS never labels fob 'group B' by hand. Early on, the Kinship Vote "
      "might be 30% B, 25% A, 20% Stranger and the rest spread out: OS is honestly unsure, so it borrows little. Later it "
      "might be 80% B, because B's past members keep predicting fob's real data best. Inside B, the Fresh-Days Check decides "
      "between the recipes that worked for B1, B2 and so on: they compete on fob's own newest data, and the best one wins."),

    P("5. Why trust it? The Time Machine Replay", s_h),
    P("We pretend each past entry is fob, hide everything after it, and replay it step by step. Both case studies use the same four checks:"),
    B("<b>Right kin?</b> Did the Kinship Vote point to what, in hindsight, was most similar? Sanity checks: a flu season "
      "should pick flu seasons; a viral-vector vaccine should lean on viral-vector vaccines."),
    B("<b>Honest confidence?</b> When OS says '80% B', it should be right about 80% of the time."),
    B("<b>Earlier and better?</b> OS must beat the baselines: real data alone in Case Study 1, and the standard safety "
      "methods in Case Study 2. We report the <b>worst</b> case, not just the average."),
    B("<b>Honest Green Light?</b> Whenever the light was green, OS really was ready (within 0.02 of the gold standard in "
      "Case Study 1; a real signal, not a false alarm, in Case Study 2)."),

    P("6. Case Study 1: early outbreak data (in progress)", s_h),
    P("Data: Brazil's national surveillance of hospitalised severe respiratory illness (SIVEP-Gripe), Ministry of Health, "
      "CC-BY, 2009–2022. Task: predict in-hospital death from what is known at admission."),
    table([
        ["Finding so far", "Number"],
        ["Real data alone: plateau day for COVID-19 (2020)", "day 33 (2,824 patients)"],
        ["Real data alone: plateau day for H1N1 (2009)", "day 56 (7,315 patients)"],
        ["Days with too little data to train at all", "COVID days 0–20, H1N1 days 0–26"],
        ["Model trained only on pre-2020 outbreaks, scored on COVID", "AUC 0.727, but age alone also gives 0.727"],
        ["Death rate: past outbreaks vs COVID", "11.5% vs 33.6%"],
    ], [4.6 * inch, 2.4 * inch]),
    Spacer(1, 4),
    P("This is why OS is designed this way. Borrowing everything from the past taught OS only 'older patients die more'. "
      "And copying the past's death rate would have shown a third of COVID's real deaths. So the Kinship Vote chooses whom "
      "to borrow from, and the Handover Rule never borrows the overall rate."),

    P("7. Case Study 2: vaccine side-effect signals (planned)", s_h),
    P("<b>Question:</b> when a new vaccine is rolled out, can OS confirm a real side-effect signal earlier than standard "
      "methods, with no more false alarms, and point to the groups at risk so they can be protected (e.g. offered a "
      "different vaccine or dose schedule)?"),
    P("<b>Replay cases</b> (signals later confirmed as real; detection dates to be verified from primary sources):"),
    B("Myocarditis in young men after mRNA COVID-19 vaccines."),
    B("Rare blood clots with low platelets after viral-vector COVID-19 vaccines."),
    B("Narcolepsy after the Pandemrix vaccine for 2009 H1N1."),
    B("Bowel blockage (intussusception) in infants after the RotaShield rotavirus vaccine (1999)."),
    P("<b>Data to check first</b> (download, licence, fields):"),
    B("<b>VAERS (US)</b>: public and downloadable. Anyone can report, a report does not prove the vaccine caused the event, "
      "and it has no dose counts, so dose counts must come from separate public figures."),
    B("<b>Brazil's vaccine adverse-event reports</b>: possibly on the same Ministry of Health portal as Case Study 1. Not yet checked."),
    B("Richer but restricted, needing an application: WHO VigiBase, the US Vaccine Safety Datalink, and clinical-trial data."),
    P("<b>Baselines to beat:</b> the standard safety-monitoring statistics, which compare how often an event is reported "
      "for this vaccine against all others (including Bayesian versions that already borrow strength), and sequential tests "
      "of observed against expected cases. Beating these, not just 'no model', is the bar."),
    P("<b>Expected cases matter:</b> some people would develop myocarditis or blood clots anyway. A signal means more cases "
      "than expected for that age and sex, so OS must use background rates."),

    P("8. Build order", s_h),
    table([
        ["Step", "What", "Done when"],
        ["1", "Kinship Vote + Stranger Flag (Case Study 1)", "The Time Machine Replay over all 24 outbreaks picks sensible kin"],
        ["2", "Two-Part Recipe + Handover Rule (Case Study 1)", "COVID 2020 replay reaches the plateau before day 33"],
        ["3", "Fresh-Days Check + Green Light (Case Study 1)", "The Green Light is honest in every replay"],
        ["4", "Data check for Case Study 2 (VAERS, Brazil)", "We know what is downloadable, its licence and its fields"],
        ["5", "Vaccine Atlas + week-by-week replay of known signals", "We know when standard methods would have flagged each signal"],
        ["6", "Run the same OS parts on Case Study 2", "OS flags real signals earlier with no more false alarms, or we report that it does not"],
        ["7", "Synth Release + Glass Box Report (both)", "Synthetic data matches real data side by side and is labelled synthetic"],
        ["8", "More outbreaks and vaccines (mpox, Ebola, SARS, MERS, other countries)", "OS is tested well beyond the first examples"],
    ], [0.5 * inch, 3.0 * inch, 3.5 * inch]),

    P("9. Limits we say up front", s_h),
    B("Synthetic rows hold no more information than fob's real data plus what OS learned from the past. Ten million rows "
      "is a format, not new knowledge. The Stranger Flag and the Green Light keep OS honest about this."),
    B("<b>Synthetic data cannot reveal a side effect nobody has reported yet.</b> Rare events (1 in 100,000 doses) are exactly "
      "what generators wash out. In Case Study 2, OS's job is to catch real signals earlier and find who is at risk. Synthetic "
      "data is a supporting tool (testing detection methods, planning monitoring), never a replacement for real safety evidence "
      "or clinical trials."),
    B("<b>Mislabelled synthetic data can do harm.</b> Synthetic side-effect data that looks real could be passed around as "
      "evidence that vaccines are dangerous. Every synthetic file is clearly labelled, and nothing is fabricated or presented as real."),
    B("A vaccine-safety report is not proof that the vaccine caused the event. OS's conclusions are signals for experts to "
      "investigate, explained in the Glass Box Report, not verdicts."),
    B("The Outbreak Atlas has 24 outbreaks but only about 4 truly different diseases, and confirmed vaccine signals are few. "
      "That is the real sample size behind any claim of trust, which is why adding more cases is part of the plan."),
    B("Some things make cases look alike for the wrong reasons: form changes (the 2019+ outbreak form leaves far more fields "
      "blank), unusual first patients, changes in testing, and surges in reporting after media coverage. The Kinship Vote has "
      "to correct for these, and the replays check that it did."),
]

doc = SimpleDocTemplate("docs/outbreak-synth-plan.pdf", pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                        topMargin=0.7 * inch, bottomMargin=0.8 * inch, title="Outbreak Synth (OS): plan v2",
                        author="outbreak-synth project")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("wrote docs/outbreak-synth-plan.pdf")
