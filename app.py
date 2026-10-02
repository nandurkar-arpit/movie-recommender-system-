"""Afterglow UI (animated). Run:  streamlit run app.py   (API must be running: uvicorn main:app)"""
import html
import os

import requests
import streamlit as st
import streamlit.components.v1 as components

API = os.getenv("API_URL", "http://127.0.0.1:8000")
MODES = ["Similar to a film", "Describe a mood"]
esc = html.escape

st.set_page_config(page_title="Afterglow", page_icon="🎞️", layout="wide")

# ───────────────────────── design tokens + styles ─────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap');
:root{--bg:#161C28;--rail:#111621;--s1:rgba(255,255,255,.035);--s2:rgba(255,255,255,.065);
--line:rgba(255,255,255,.09);--ink:#ECE9E2;--mute:#9AA3B2;--faint:#677185;
--amber:#E9B15B;--steel:#8FB8DE;--ok:#5FD3A3;--bad:#E58A7B;--ease:cubic-bezier(.2,.7,.2,1)}
@property --a{syntax:'<angle>';inherits:false;initial-value:0deg}
html,body,.stApp,[class*="st-"],button,input,textarea{font-family:'Geist',ui-sans-serif,system-ui,sans-serif}
.stApp{background:var(--bg);color:var(--ink);font-feature-settings:"ss01","cv11";isolation:isolate}
[data-testid="stToolbar"],footer{display:none!important}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1120px;padding:2.75rem 2.5rem 5rem}
[data-testid="stSidebar"]{background:var(--rail);border-right:1px solid var(--line)}
[data-testid="stSidebar"] .block-container,[data-testid="stSidebarUserContent"]{padding-top:1.5rem}
.stApp a{text-decoration:none;color:inherit}
.stApp a:focus-visible,.stApp input:focus-visible{outline:2px solid var(--steel);outline-offset:2px}
.stApp iframe[height="0"]{position:absolute;width:0;height:0;border:0}

/* ambient: drifting light, film grain, cursor glow */
.stApp::before{content:"";position:fixed;inset:-25%;z-index:-1;pointer-events:none;will-change:transform;
background:radial-gradient(38% 32% at 18% 22%,rgba(233,177,91,.17),transparent 70%),
radial-gradient(34% 38% at 82% 28%,rgba(143,184,222,.15),transparent 70%),
radial-gradient(40% 30% at 55% 90%,rgba(229,138,123,.09),transparent 70%);animation:drift 26s ease-in-out infinite alternate}
.stApp::after{content:"";position:fixed;inset:-20%;z-index:60;pointer-events:none;opacity:.065;
background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
animation:jitter .9s steps(1) infinite}
.ag-cursor{position:fixed;top:0;left:0;width:440px;height:440px;border-radius:50%;pointer-events:none;z-index:1;opacity:0;
background:radial-gradient(circle,rgba(233,177,91,.10),transparent 65%);transition:transform .22s ease-out,opacity .4s}

/* keyframes */
@keyframes drift{to{transform:translate3d(5%,3%,0) rotate(7deg) scale(1.1)}}
@keyframes jitter{0%{transform:translate(0,0)}20%{transform:translate(-3%,2%)}40%{transform:translate(2%,-3%)}60%{transform:translate(-2%,-1%)}80%{transform:translate(3%,3%)}}
@keyframes rise{from{opacity:0;transform:translateY(22px) scale(.985);filter:blur(6px)}}
@keyframes sheen{from{background-position:100% 0}to{background-position:-100% 0}}
@keyframes flow{0%{background-position:0% 50%}100%{background-position:100% 50%}}
@keyframes ping{to{transform:scale(3.4);opacity:0}}
@keyframes blip{0%{box-shadow:0 0 0 0 rgba(95,211,163,.55)}100%{box-shadow:0 0 0 9px rgba(95,211,163,0)}}
@keyframes spin{to{--a:360deg}}
@keyframes grow{from{transform:scaleX(0)}}
@keyframes float{50%{transform:translateY(-6px)}}

/* entrance: everything staggers in by --i */
.hero h1,.hero p,.sect,.anchor,.card,.row,.notice{animation:rise .85s var(--ease) calc(var(--i,0)*70ms) backwards}
.hero p{animation-delay:.25s}.sect{animation-delay:.1s}

/* sidebar */
.brand{display:flex;align-items:center;gap:10px;font-size:20px;font-weight:600;letter-spacing:-.045em}
.mark{position:relative;width:9px;height:9px;border-radius:50%;background:var(--amber);box-shadow:0 0 0 4px rgba(233,177,91,.15),0 0 18px rgba(233,177,91,.7)}
.mark::after{content:"";position:absolute;inset:0;border-radius:50%;border:1px solid var(--amber);animation:ping 2.4s ease-out infinite}
.status{display:flex;align-items:center;gap:8px;margin:14px 0 26px;font-size:12px;color:var(--mute)}
.status i{width:6px;height:6px;border-radius:50%;background:var(--ok);animation:blip 2s ease-out infinite}
.status.off i{background:var(--bad);animation:none}
.fine{font-size:11px;line-height:1.55;color:var(--faint);margin-top:28px}
[data-testid="stSidebar"] label p{font-size:12.5px;color:var(--mute)}

/* inputs */
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-baseweb="select"]>div{
background:var(--s1)!important;border:1px solid var(--line)!important;border-radius:10px!important;color:var(--ink)!important;
transition:border-color .25s,box-shadow .25s,background .25s,transform .25s var(--ease)}
[data-testid="stTextInput"] input{padding:.8rem 1rem;font-size:15px}
[data-testid="stTextInput"] input:hover,[data-testid="stTextArea"] textarea:hover{background:var(--s2)!important}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus{border-color:rgba(143,184,222,.6)!important;
box-shadow:0 0 0 4px rgba(143,184,222,.12),0 10px 30px -10px rgba(143,184,222,.35)!important;transform:translateY(-1px)}
.stButton button,[data-testid="stFormSubmitButton"] button{color:#161C28;border:0;border-radius:10px;font-weight:500;padding:.55rem 1.1rem;
background:linear-gradient(100deg,var(--ink) 0 38%,#FFE7B3 50%,var(--ink) 62% 100%) 100% 0/200% 100%;
transition:transform .2s var(--ease),box-shadow .25s}
.stButton button:hover,[data-testid="stFormSubmitButton"] button:hover{color:#161C28;transform:translateY(-2px);
box-shadow:0 12px 28px -8px rgba(233,177,91,.55);animation:sheen .9s ease}
.stButton button:active,[data-testid="stFormSubmitButton"] button:active{transform:scale(.96)}
[data-testid="stForm"]{border:0;padding:0}

/* type */
.hero{max-width:640px;margin:1.5rem 0 2.25rem}
.hero h1{font-size:clamp(2rem,4.2vw,3.3rem);line-height:1.02;font-weight:600;letter-spacing:-.05em;margin:0 0 1rem;padding:0 0 .1em;
background:linear-gradient(100deg,var(--ink) 0 36%,var(--amber) 45%,#fff 50%,var(--steel) 55%,var(--ink) 64% 100%) 100% 0/200% 100%;
-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
animation:rise .95s var(--ease) backwards,sheen 7s linear 1s infinite}
.hero p,.lede{font-size:15.5px;line-height:1.6;color:var(--mute);max-width:54ch;margin:0}
.sect{display:flex;align-items:baseline;justify-content:space-between;gap:16px;margin:2.5rem 0 1rem}
.sect h4{font-size:15px;font-weight:600;letter-spacing:-.02em;margin:0;padding:0}
.sect span{font-size:12.5px;color:var(--faint)}
.num,.rate,.rk{font-variant-numeric:tabular-nums}

/* atoms */
.poster{position:relative;display:block;aspect-ratio:2/3;border-radius:8px;overflow:hidden;background:var(--s2);border:1px solid var(--line);
transition:transform .5s var(--ease),box-shadow .45s}
.poster img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .7s var(--ease)}
.poster::after{content:"";position:absolute;inset:0;pointer-events:none;transform:translateX(-130%);
background:linear-gradient(110deg,transparent 35%,rgba(255,255,255,.26) 50%,transparent 65%);transition:transform .9s var(--ease)}
.card:hover .poster,.row:hover .poster,.anchor:hover .poster{transform:scale(1.04) rotate(-1.2deg);box-shadow:0 18px 40px -12px rgba(233,177,91,.4)}
.card:hover .poster img,.anchor:hover .poster img{transform:scale(1.09)}
.card:hover .poster::after,.row:hover .poster::after,.anchor:hover .poster::after{transform:translateX(130%)}
.poster.ph{display:grid;place-items:center;font-weight:600;font-size:22px;letter-spacing:-.04em;color:var(--faint);
background:linear-gradient(135deg,var(--s2),rgba(143,184,222,.16),rgba(233,177,91,.12),var(--s2));background-size:300% 300%;animation:flow 7s ease-in-out infinite alternate}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:11.5px;padding:2px 9px;border:1px solid var(--line);border-radius:999px;color:var(--mute);transition:transform .2s var(--ease),color .2s,border-color .2s}
.chip:hover{transform:translateY(-2px);color:var(--ink);border-color:rgba(255,255,255,.3)}
.chip.on{color:var(--ink);border-color:rgba(143,184,222,.5);background:rgba(143,184,222,.1)}
.meta{display:flex;align-items:center;gap:12px;font-size:12.5px;color:var(--faint)}
.rate{color:var(--amber);font-weight:500;text-shadow:0 0 14px rgba(233,177,91,.45)}.rate.none{color:var(--faint);text-shadow:none}
.meter-wrap{display:flex;align-items:center;gap:10px}
.meter-wrap .num{font-size:12px;color:var(--mute);min-width:30px}
.meter{display:block;flex:1;height:3px;background:var(--line);border-radius:3px;overflow:hidden}
.meter i{display:block;height:100%;border-radius:3px;transform-origin:left;
background:linear-gradient(90deg,var(--steel) 0 35%,#D9ECFF 50%,var(--steel) 65% 100%) 100% 0/200% 100%;
box-shadow:0 0 12px rgba(143,184,222,.6);animation:grow 1s var(--ease) .35s backwards,sheen 2.8s linear infinite}
.blurb{font-size:13.5px;line-height:1.6;color:var(--mute);margin:0;display:-webkit-box;-webkit-box-orient:vertical;overflow:hidden}
.why{font-size:12.5px;color:var(--faint);margin:0}
.go{font-size:12.5px;color:var(--steel)!important;width:max-content;background:linear-gradient(var(--steel),var(--steel)) 0 100%/0 1px no-repeat;
padding-bottom:2px;transition:background-size .35s var(--ease),letter-spacing .35s var(--ease)}
.go:hover{background-size:100% 1px;letter-spacing:.02em}

/* glow layers shared by anchor, cards and rows: spotlight follows the cursor, edge light orbits */
.anchor,.card,.row{position:relative}
.anchor,.card{overflow:hidden}
.anchor::before,.card::before,.row::before{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;opacity:0;transition:opacity .35s;
background:radial-gradient(340px circle at var(--mx,50%) var(--my,0%),rgba(233,177,91,.17),transparent 62%)}
.anchor:hover::before,.card:hover::before,.row:hover::before{opacity:1}
.anchor::after,.card::after{content:"";position:absolute;inset:0;border-radius:inherit;padding:1px;pointer-events:none;opacity:0;transition:opacity .4s;
background:conic-gradient(from var(--a),transparent 0 62%,var(--amber) 80%,var(--steel) 92%,transparent);
-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;animation:spin 5s linear infinite}
.card:hover::after,.card.lead::after,.anchor::after{opacity:1}

/* anchor panel */
.anchor{display:grid;grid-template-columns:168px minmax(0,1fr);gap:28px;padding:24px;border:1px solid var(--line);border-radius:14px;background:var(--s1)}
.anchor .poster{box-shadow:0 20px 50px -18px rgba(233,177,91,.35);animation:float 6s ease-in-out infinite}
.anchor h2{font-size:clamp(1.6rem,3vw,2.3rem);font-weight:600;letter-spacing:-.045em;line-height:1.05;margin:0;padding:0}
.anchor .tagline{font-size:15px;color:var(--ink);opacity:.8;margin:0;font-style:italic}
.anchor .body{display:flex;flex-direction:column;gap:14px;justify-content:center}
.anchor .blurb{-webkit-line-clamp:4;max-width:62ch}

/* results: one lead, two supporting, then a ranked list */
.feat{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(0,1fr);gap:16px}
.card{display:grid;gap:18px;padding:20px;border:1px solid var(--line);border-radius:14px;background:var(--s1);
transition:background .2s,border-color .2s,transform .4s var(--ease),box-shadow .4s}
.card:hover{background:var(--s2);border-color:rgba(255,255,255,.16);transform:translateY(-5px);box-shadow:0 26px 50px -26px rgba(0,0,0,.7)}
.card .body{display:flex;flex-direction:column;gap:10px;min-width:0}
.card h3{font-weight:600;letter-spacing:-.035em;line-height:1.1;margin:0;padding:0}
.card .go{margin-top:auto}
.card.lead{grid-row:span 2;grid-template-columns:150px minmax(0,1fr);padding:24px}
.card.lead h3{font-size:1.7rem}.card.lead .blurb{-webkit-line-clamp:5}
.card.mid{grid-template-columns:84px minmax(0,1fr)}
.card.mid h3{font-size:1.1rem}.card.mid .blurb{-webkit-line-clamp:2}
.list{margin-top:16px;border:1px solid var(--line);border-radius:14px;overflow:hidden}
.row{display:grid;grid-template-columns:22px 44px minmax(0,1fr) auto 118px;gap:16px;align-items:center;padding:12px 18px;border-top:1px solid var(--line);
box-shadow:inset 0 0 0 var(--amber);transition:background .2s,transform .3s var(--ease),box-shadow .3s}
.row:first-child{border-top:0}.row:hover{background:var(--s2);transform:translateX(5px);box-shadow:inset 3px 0 0 var(--amber)}
.plain .row{grid-template-columns:44px minmax(0,1fr) auto}
.row .rk{font-size:12.5px;color:var(--faint);transition:color .2s}.row:hover .rk{color:var(--amber)}
.row .t{display:flex;flex-direction:column;gap:2px;min-width:0}
.row .t b{font-weight:500;font-size:14.5px;letter-spacing:-.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.row .t small{font-size:12px;color:var(--faint)}
.row .poster{border-radius:5px}

.notice{display:flex;flex-direction:column;gap:4px;padding:16px 18px;border:1px solid var(--line);border-left:2px solid var(--amber);border-radius:10px;background:var(--s1);font-size:13.5px;color:var(--mute);margin-top:1rem}
.notice b{color:var(--ink);font-weight:500}.notice code{font-size:12.5px;color:var(--steel)}

@media (max-width:860px){
.block-container{padding:2rem 1.25rem 4rem}
.feat{grid-template-columns:1fr}.card.lead{grid-row:auto;grid-template-columns:110px minmax(0,1fr)}
.anchor{grid-template-columns:104px minmax(0,1fr);gap:18px;padding:16px}
.row{grid-template-columns:20px 40px minmax(0,1fr) auto}.row .meter-wrap{display:none}}
@media (prefers-reduced-motion:reduce){
*,*::before,*::after{animation:none!important;transition:none!important}
.hero h1{-webkit-text-fill-color:var(--ink);background:none}.ag-cursor{display:none}}
"""

# Cursor glow + per-card spotlight. Streamlit strips <script> from markdown, so this runs from a 0-height component.
FX = """<script>
const d=window.parent.document;
if(!d.__afterglow){d.__afterglow=1;
const g=d.createElement('div');g.className='ag-cursor';d.body.appendChild(g);
d.addEventListener('mousemove',e=>{
  g.style.opacity=1;g.style.transform=`translate3d(${e.clientX-220}px,${e.clientY-220}px,0)`;
  const t=e.target.closest&&e.target.closest('.card,.row,.anchor');
  if(t){const r=t.getBoundingClientRect();t.style.setProperty('--mx',(e.clientX-r.left)+'px');t.style.setProperty('--my',(e.clientY-r.top)+'px');}
},{passive:true});
d.documentElement.addEventListener('mouseleave',()=>{g.style.opacity=0});}
</script>"""


# ───────────────────────────── data access ─────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def _get(path: str, params: dict):
    r = requests.get(f"{API}{path}", params=params, timeout=25)
    r.raise_for_status()
    return r.json()  # exceptions are never cached, so a restarted API recovers instantly


def api(path: str, **params):
    try:
        return _get(path, {k: v for k, v in params.items() if v is not None})
    except requests.RequestException:
        return None


def health():
    try:
        return requests.get(f"{API}/health", timeout=2).json()
    except requests.RequestException:
        return None


# ───────────────────────────── components ─────────────────────────────
def stagger(i):
    return f' style="--i:{min(int(i or 0), 14)}"'


def poster(m, cls=""):
    if m.get("poster"):
        return f'<span class="poster {cls}"><img src="{esc(m["poster"])}" alt="Poster for {esc(m["title"])}" loading="lazy"></span>'
    initials = "".join(w[0] for w in m["title"].split()[:2]).upper()
    return f'<span class="poster ph {cls}" aria-hidden="true">{esc(initials)}</span>'


def rating(m):
    if m["rating"] > 0:
        return f'<span class="rate" title="Average TMDB user rating, out of 10">★ {m["rating"]:.1f}</span>'
    return '<span class="rate none" title="Not enough votes for a rating">Unrated</span>'


def chips(genres, on=frozenset(), limit=4):
    if not genres:
        return ""
    return '<div class="chips">' + "".join(
        f'<span class="chip{" on" if g in on else ""}">{esc(g)}</span>' for g in genres[:limit]) + "</div>"


def meter(score, top):
    w = max(6, round(score / top * 100)) if top else 0
    tip = f"Cosine similarity {score:.3f}. Higher means closer plot wording and genre overlap."
    return f'<span class="meter-wrap" title="{tip}"><span class="num">{score:.2f}</span><span class="meter"><i style="width:{w}%"></i></span></span>'


def why(m, on):
    shared = [g for g in m["genres"] if g in on]
    if not on:
        return "Closest to your description"
    if not shared:
        return "Matched on plot wording, not genre"
    joined = shared[0] if len(shared) == 1 else ", ".join(
        shared[:-1]) + " and " + shared[-1]
    return f"Shares {esc(joined)}"


def year(m):
    return f'<span class="num">{m["year"]}</span>' if m.get("year") else ""


def card(m, kind, top, on, i=0):
    text = m["overview"] or m["tagline"] or "No synopsis on file for this title."
    return (f'<div class="card {kind}"{stagger(i)}>{poster(m)}<div class="body">'
            f'<div class="meta">{rating(m)}{year(m)}</div>'
            f'<h3>{esc(m["title"])}</h3>{chips(m["genres"], on)}'
            f'<p class="blurb">{esc(text)}</p><p class="why">{why(m, on)}</p>'
            f'{meter(m["score"], top)}'
            f'<a class="go" href="?movie={m["id"]}" target="_self">Explore from here</a></div></div>')


def row(m, rank, top, i=0):
    right = meter(m["score"], top) if m.get("score") is not None else ""
    lead = f'<span class="rk">{rank}</span>' if rank else ""
    return (f'<a class="row"{stagger(i)} href="?movie={m["id"]}" target="_self" title="Use {esc(m["title"])} as your starting film">'
            f'{lead}{poster(m)}<span class="t"><b>{esc(m["title"])}</b>'
            f'<small>{esc(", ".join(m["genres"][:3]) or "No genre listed")}</small></span>{rating(m)}{right}</a>')


def anchor_panel(m):
    tag = f'<p class="tagline">{esc(m["tagline"])}</p>' if m["tagline"] else ""
    return (f'<div class="anchor">{poster(m)}<div class="body">'
            f'<div class="meta">Starting from{rating(m)}{year(m)}</div>'
            f'<h2>{esc(m["title"])}</h2>{tag}{chips(m["genres"], limit=6)}'
            f'<p class="blurb">{esc(m["overview"])}</p></div></div>')


def results_block(res, on, heading, note):
    top = res[0]["score"]
    out = (f'<div class="sect"><h4>{esc(heading)}</h4><span>{esc(note)}</span></div><div class="feat">'
           + card(res[0], "lead", top, on, 1)
           + "".join(card(m, "mid", top, on, i + 1) for i, m in enumerate(res[1:3], 1)) + "</div>")
    if len(res) > 3:
        out += '<div class="list">' + \
            "".join(row(m, i, top, i)
                    for i, m in enumerate(res[3:], 4)) + "</div>"
    st.markdown(out, unsafe_allow_html=True)


def notice(title, body):
    st.markdown(
        f'<div class="notice"><b>{title}</b><span>{body}</span></div>', unsafe_allow_html=True)


def api_down():
    notice("The recommendation API isn’t responding",
           f"Start it with <code>uvicorn main:app --reload</code>, then refresh. Looking for it at <code>{esc(API)}</code>.")


# ───────────────────────────── screens ─────────────────────────────
def landing(films):
    st.markdown(
        f'<div class="hero"><h1>What to watch after the one you can’t stop thinking about.</h1>'
        f'<p>Name a film. Afterglow compares plot wording and genre across {films:,} titles and ranks the '
        f'closest matches, with the reason for each.</p></div>', unsafe_allow_html=True)
    picks = api("/popular", limit=6)
    if picks:
        st.markdown('<div class="sect"><h4>Not sure where to start?</h4><span>Well-rated films most people have seen</span></div>'
                    '<div class="list plain">' +
                    "".join(row(m, None, None, i + 2)
                            for i, m in enumerate(picks)) + "</div>",
                    unsafe_allow_html=True)


def film_mode(f, films):
    q = st.text_input(
        "Film title", placeholder="Try Inception, Spirited Away or Heat", label_visibility="collapsed")
    movie_id = None
    if q.strip():
        found = api("/search", q=q.strip(), limit=8)
        if found is None:
            return api_down()
        if not found:
            return notice(f"No title contains “{esc(q.strip())}”",
                          "Search matches any part of a title, so a shorter fragment often works.")
        if len(found) == 1:
            movie_id = found[0]["id"]
        else:
            by_id = {m["id"]: m for m in found}
            movie_id = st.selectbox(
                f"{len(found)} titles match. Pick the one you mean.", list(by_id),
                format_func=lambda i: f'{by_id[i]["title"]}  ({", ".join(by_id[i]["genres"][:2]) or "no genre listed"})')
    else:
        try:
            movie_id = int(st.query_params.get("movie", ""))
        except ValueError:
            movie_id = None
    if movie_id is None:
        return landing(films)

    st.query_params["movie"] = str(movie_id)  # makes the page a shareable link
    data = api("/recommend", movie_id=movie_id,
               top_n=f["n"], min_rating=f["rating"], genre=f["genre"])
    if data is None:
        return api_down()
    st.markdown(anchor_panel(data["anchor"]), unsafe_allow_html=True)
    if not data["results"]:
        return notice("Nothing clears your filters",
                      "Lower the minimum rating or set Genre to Any in the sidebar.")
    on = set(data["anchor"]["genres"])
    note = f'{len(data["results"])} films, ranked by similarity. Rated {f["rating"]:.1f} or higher.'
    results_block(data["results"], on, "Closest matches", note)


def mood_mode(f):
    st.markdown('<div class="hero"><h1>Describe the film you’re in the mood for.</h1>'
                '<p>Write it the way you’d tell a friend: who it follows, what goes wrong, where it’s set.</p></div>',
                unsafe_allow_html=True)
    with st.form("mood", border=False):
        text = st.text_area("Description", height=110, label_visibility="collapsed",
                            placeholder="A slow-burn heist where nobody can be trusted, set in 1970s Paris")
        go = st.form_submit_button("Find matches")
    if go and text.strip():
        st.session_state["mood"] = text.strip()
    q = st.session_state.get("mood")
    if not q:
        return
    data = api("/discover", q=q, top_n=f["n"],
               min_rating=f["rating"], genre=f["genre"])
    if data is None:
        return api_down()
    if not data["results"]:
        return notice("No usable words in that description",
                      "Add a few specifics, such as a setting, a profession or a turning point.")
    results_block(data["results"], set(
    ), "Best fits for your description", f'{len(data["results"])} films')


# ───────────────────────────── app shell ─────────────────────────────
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
h = health()
with st.sidebar:
    st.markdown('<div class="brand"><span class="mark"></span>Afterglow</div>',
                unsafe_allow_html=True)
    if h:
        poster_note = "" if h["tmdb"] else " Posters are off: add TMDB_API_KEY."
        st.markdown(
            f'<div class="status"><i></i>{h["films"]:,} films indexed.{poster_note}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="status off"><i></i>API unreachable</div>', unsafe_allow_html=True)
    mode = st.radio("Mode", MODES, label_visibility="collapsed")
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    genre_options = api("/genres") or []
    filters = {
        "rating": st.slider("Minimum rating", 0.0, 9.0, 5.0, 0.5),
        "genre": st.selectbox("Genre", ["Any"] + genre_options),
        "n": st.slider("Number of results", 5, 20, 10),
    }
    filters["genre"] = None if filters["genre"] == "Any" else filters["genre"]
    st.markdown('<p class="fine">Posters and ratings from TMDB. This product uses the TMDB API '
                'but is not endorsed or certified by TMDB.</p>', unsafe_allow_html=True)

if not h:
    api_down()
elif mode == MODES[0]:
    film_mode(filters, h["films"])
else:
    mood_mode(filters)

components.html(FX, height=0)
