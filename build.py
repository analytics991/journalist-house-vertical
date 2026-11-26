#!/usr/bin/env python3
"""Builds the static site into the repository root from src/ and data/.

  python3 build.py

src/base.html      home page + shared chrome (top menu, chapters menu, overlays, footer)
src/journey2.html  Chapter II content
src/gallery.html   residences gallery content
src/extra.css      styles added on top of the base styles
src/site.js        behaviour shared by every page
data/units.json    residences, floors and availability (copied from the old site)
data/legal.json    terms, privacy and accessibility texts (copied from the old site)
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
CDN = 'https://cdn.prod.website-files.com/6a4f7045e10baec12b17db43'
OLD = 'https://www.journalist-house.com/'


def read(p):
    with open(os.path.join(ROOT, p), encoding='utf-8') as f:
        return f.read()


def write(p, s):
    full = os.path.join(ROOT, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(s)


def between(s, a, b, include=False):
    i = s.index(a)
    j = s.index(b, i + len(a))
    return s[i:j + len(b)] if include else s[i + len(a):j]


base = read('src/base.html')
CSS = between(base, '<style>\n', '</style>') + read('src/extra.css')
FONTS = between(base, '<link rel="icon"', '<script>', False)
FONTS = '<link rel="icon"' + FONTS
SYMBOLS = between(base, '<svg width="0" height="0"', '</svg>\n\n<!-- ================= TOP MENU', True)
SYMBOLS = SYMBOLS[:SYMBOLS.rindex('</svg>') + 6]
TOPBAR = between(base, '<header class="topbar">', '</header>', True)
MENU = between(base, '<div class="menu" id="menu"', '\n\n<main>', True)[:-len('\n\n<main>')]
HOME_MAIN = between(base, '<main>\n', '</main>')
FOOTER = between(base, '<footer class="foot">', '</footer>', True)
MODAL = between(base, '<div class="modal" id="inquire"', '<!-- ================= VIDEO', True)
MODAL = MODAL[:MODAL.rindex('<!--')]
VIDEO_COOKIES = between(base, '<div class="modal vid"', '<script>\n(function', True)
VIDEO_COOKIES = VIDEO_COOKIES[:VIDEO_COOKIES.rindex('<script>')]

# the form, reusable in the overlay and in-page
FORM = between(MODAL, '<form id="inqForm" novalidate>', '</form>', True)
FORM = FORM.replace('<form id="inqForm" novalidate>', '<form class="inq-f" novalidate>\n        <input type="hidden" name="Residence" value="">')
NOTE = '<div class="inq-note" aria-live="polite"><b></b><span></span></div>'
MODAL = re.sub(r'<form id="inqForm".*?</form>\s*<div class="inq-note".*?</div>', lambda m: FORM + '\n      ' + NOTE, MODAL, flags=re.S)
MODAL = MODAL.replace(' id="inqBox"', '')

NIGHT = re.sub(r'^<svg[^>]*>', '<svg viewBox="0 0 1332 741" fill="none" aria-hidden="true">', read('src/night-labels.svg').strip())
HOME_MAIN = HOME_MAIN.replace('{NIGHT_SVG}', NIGHT)
import hashlib
VERSION = hashlib.md5((CSS + read('src/site.js')).encode('utf-8')).hexdigest()[:8]
HERO = re.search(r'  <!-- =+ HERO =+ -->\n  <section class="hero".*?</section>\n', HOME_MAIN, re.S).group(0)
HOME_MAIN = HOME_MAIN.replace(HERO, '')


def localise(s, R, page):
    """Point every link at the local copy."""
    home = '' if page == 'index' else R + 'index.html'
    j2 = '' if page == 'journey-2' else R + 'journey-2.html'
    s = re.sub(r'href="#(the-project|the-architects|the-location|the-building|the-residences|top)"',
               lambda m: 'href="%s#%s"' % (home, m.group(1)), s)
    s = re.sub(re.escape(OLD) + r'journey-2#([\w-]+)', lambda m: '%s#%s' % (j2, m.group(1)), s)
    s = re.sub(re.escape(OLD) + r'([\w-]+)', lambda m: R + m.group(1) + '.html', s)
    s = s.replace('href="/privacy-policy"', 'href="%sprivacy-policy.html"' % R)
    s = s.replace('href="/accessibility-statement"', 'href="%saccessibility-statement.html"' % R)
    s = s.replace('href="/terms-of-use"', 'href="%sterms-of-use.html"' % R)
    return s.replace('{V}', VERSION).replace('{R}', R).replace('@/', CDN + '/').replace('@%2F', CDN + '%2F')


def contact(R):
    return ('<section class="contact" id="inquire-form">\n'
            '    <div class="inq-img"><img loading="lazy" src="%s/6a61ea6b52fd4d666ef879f9_Contact%%20Us%%20%%7C%%20Visual.avif" alt=""></div>\n'
            '    <div class="inq-form">\n      %s\n      %s\n    </div>\n  </section>' % (CDN, FORM, NOTE))


def page(path, title, desc, main, chapter_label='', chapters=(), before_main='', page_id=''):
    R = '../' * path.count('/')
    top = TOPBAR
    if chapters:
        top = top.replace('<span>CHAPTER I:</span><span id="chName">THE PROJECT</span>',
                          '<span>%s</span><span id="chName">%s</span>' % (chapter_label, chapters[0]))
    else:
        top = re.sub(r'<div class="tb-chapter".*?</div>\s*</div>\s*</div>', '', top, flags=re.S)
    main = main.replace('{CONTACT}', contact(R))
    doc = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
%s<script>document.documentElement.className += ' js';document.documentElement.className += ' ld-on';</script>
<link rel="stylesheet" href="{R}css/site.css?v={V}">
</head>
<body id="top" data-chapters="%s">

%s
<div class="ld" id="ld" aria-hidden="true"><div class="ld-logo"><svg class="ld-base" viewBox="0 0 306 150"><use href="#jh-logo"/></svg><svg class="ld-fill" viewBox="0 0 306 150"><use href="#jh-logo"/></svg></div></div>

%s

%s

%s<main>
%s</main>

%s

%s
%s
<script src="{R}js/site.js?v={V}"></script>
</body>
</html>
''' % (html.escape(title), html.escape(desc, quote=True), FONTS, html.escape('|'.join(chapters), quote=True),
       SYMBOLS, top, MENU, before_main, main, FOOTER, MODAL, VIDEO_COOKIES)
    write(path, localise(doc, R, page_id))


CHEV = '<svg viewBox="0 0 40 59"><use href="#chev"/></svg>'

# ---------------------------------------------------------------- home
home_main = HOME_MAIN.replace('<section id="the-residences" class="tower" data-chapter="4">',
                              '<section id="the-residences" class="tower" data-pinned data-chapter="4">')
page('index.html',
     'Journalist House - בית העיתונאים | Foster + Partners Tower, Tel Aviv',
     "Journalist House – a new landmark in Tel Aviv's cultural heart, designed by Foster + Partners and Bar Orian Architects.",
     home_main, 'CHAPTER I:',
     ['THE PROJECT', 'THE ARCHITECTS', 'THE LOCATION', 'THE BUILDING', 'THE RESIDENCES'],
     before_main=HERO, page_id='index')

# ---------------------------------------------------------------- chapter II
page('journey-2.html', 'The Wellness Sanctuary | Urban Retreat in Tel Aviv',
     "Chapter II of Journalist House: the Sanctuary, the Piazza, the History and the purchasing group.",
     read('src/journey2.html'), 'CHAPTER II:',
     ['THE SANCTUARY', 'THE PIAZZA', 'THE HISTORY', 'ABOUT US'], page_id='journey-2')

# ---------------------------------------------------------------- gallery + inquire
page('see-the-residences.html', 'The Residences | Luxury Tel Aviv Apartments & Penthouses',
     'A gallery of the residences at Journalist House, Tel Aviv: Garden Terraces, Urban Residences, Double-Height Villas, Crown Residences and the Penthouse.',
     '', before_main=read('src/gallery.html'))
page('inquire.html', 'Inquire | Journalist House Tel Aviv',
     'Inquire about a residence at Journalist House, 8 Shaul HaMelech St., Tel Aviv.',
     '  {CONTACT}\n'.replace('class="contact"', 'class="contact"'))

# ---------------------------------------------------------------- legal
legal = json.loads(read('data/legal.json'))
for slug, d in legal.items():
    page(slug + '.html', d['title'], d['desc'] or d['h1'],
         '  <article class="legal">\n    <h1>%s</h1>\n    <div class="legal-text">%s</div>\n  </article>\n'
         % (html.escape(d['h1']), d['html']))

# ---------------------------------------------------------------- residence selector (original pages)
def joined(prefix, n):
    return ''.join(read('data/%s.part%d' % (prefix, i)).rstrip('\n') for i in range(n))


orig = json.loads(joined('orig', 4))
aptd = json.loads(joined('apt', 3))
GSAP = ('<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>\n'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>')


def embed(pg, cls):
    return ''.join(e['h'] for e in pg['embeds'] if e['c'].startswith(cls))


def orig_js(name):
    js = orig['js']['https://jurnalist-house-2026.vercel.app/pages/' + name]
    js = re.sub(r'"/(apartments/|floors/[a-z]*|cubes/[a-z-]*|select-a-residence)"', r'(window.JH_BASE+"\1")', js)
    js = js.replace('decodeURIComponent(t[t.length-1])', 'decodeURIComponent(t[t.length-1]).replace(/\\.html$/,"")')
    js = re.sub(r'\n//# sourceMappingURL=.*', '', js)
    write('js/orig/' + name, js)


for n in ('plans.js', 'cubes.js', 'floors.js', 'apartments.js'):
    orig_js(n)
write('css/orig.css', orig['css'])

ORIG_OVERRIDES = """
<style>
  body.orig main{max-width:none}
  body.orig main img{display:inline-block}
  body.orig .main-wrapper{min-height:calc(100vh - var(--bar))}
  body.orig .section_plans-hero{min-height:calc(100svh - var(--bar))}
  @media (min-width:992px){
    body.orig .section_units{width:100%;height:calc(100vh - var(--bar))}
    body.orig .building-mockup-div{height:calc(100vh - var(--bar))}
  }
  @media (max-width:991px){
    body.orig .section_plans-hero,body.orig .section_units{padding-top:3rem}
    body.orig .back-btn{top:1rem}
  }
</style>"""


def orig_links(h, R):
    h = re.sub(r'href="/(apartments|floors|cubes)/([\w-]+)"', lambda m: 'href="%s%s/%s.html"' % (R, m.group(1), m.group(2)), h)
    h = h.replace('href="/select-a-residence"', 'href="%sselect-a-residence.html"' % R)
    h = re.sub(r'href="/#[\w-]*"', 'href="%sindex.html#the-residences"' % R, h)
    return h


def orig_page(path, pg, main, script, title=None, desc='', page_css=None):
    R = '../' * path.count('/')
    top = re.sub(r'<div class="tb-chapter".*?</div>\s*</div>\s*</div>', '', TOPBAR, flags=re.S)
    doc = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
%s<script>(function(){var d=document.documentElement,m=/[/](cubes|floors|apartments)[/]/;d.className+=' js';try{var r=document.referrer?new URL(document.referrer):null,to=m.exec(location.pathname),from=r&&r.host===location.host?m.exec(r.pathname):null;if(to&&from&&!(to[1]==='apartments'&&from[1]!=='apartments')){d.className+=' no-ld';return;}}catch(e){}d.className+=' ld-on';})();</script>
<link rel="stylesheet" href="{R}css/orig.css?v={V}">
<link rel="stylesheet" href="{R}css/site.css?v={V}">
%s
%s
%s
</head>
<body id="top" class="orig" data-chapters="">

%s
<div class="ld" id="ld" aria-hidden="true"><div class="ld-logo"><svg class="ld-base" viewBox="0 0 306 150"><use href="#jh-logo"/></svg><svg class="ld-fill" viewBox="0 0 306 150"><use href="#jh-logo"/></svg></div></div>

%s

%s

<div class="page-wrapper"><main class="main-wrapper">%s</main></div>

%s
%s
%s
<script>window.JH_BASE = new URL('%s', location.href).pathname;</script>
<script src="{R}js/orig/%s?v={V}"></script>
<script src="{R}js/site.js?v={V}"></script>
</body>
</html>
""" % (html.escape(title or pg['title']), html.escape(desc, quote=True), FONTS,
       embed(pg, 'global-css'), page_css if page_css is not None else embed(pg, 'page-styles'), ORIG_OVERRIDES,
       SYMBOLS, top, MENU, orig_links(main, R), MODAL, VIDEO_COOKIES, GSAP, R or './', script)
    write(path, localise(doc, R, ''))


pages = orig['pages']
orig_page('select-a-residence.html', pages['/select-a-residence'], pages['/select-a-residence']['main'], 'plans.js',
          desc='Choose a section, floor and residence at Journalist House, Tel Aviv.')
n_orig = 1
for pth, pg in pages.items():
    if pth.startswith('/cubes/'):
        orig_page(pth[1:] + '.html', pg, pg['main'], 'cubes.js'); n_orig += 1
    elif pth.startswith('/floors/'):
        orig_page(pth[1:] + '.html', pg, pg['main'], 'floors.js'); n_orig += 1
apt_pg = pages['/apartments/601']
for a in aptd['apts']:
    m = re.sub(r'<!--SHARED:([\w]+)-->', lambda mm: aptd['shared'][mm.group(1)], a['main'])
    m = m.replace('<button type="button" class="inquite-button', '<button type="button" data-inquire data-unit="%s" class="inquite-button' % a['slug'])
    sec = re.search(r'mt-el="ctx-type"[^>]*>([^<]*)<', a['main'])
    pcss = embed(apt_pg, 'page-styles').replace("[mt-unit-floor='Urban Residences']", "[mt-unit-floor='%s']" % (sec.group(1).strip() if sec else ''))
    pcss = pcss.replace("[href='/apartments/601']", "[href$='apartments/%s.html'].units-nav__top-view-link" % a['slug'])
    orig_page('apartments/%s.html' % a['slug'], apt_pg, m, 'apartments.js', title=a['title'], desc=a['desc'], page_css=pcss); n_orig += 1
apts = aptd['apts']

write('css/site.css', CSS)
write('js/site.js', read('src/site.js'))
write('.nojekyll', '')
print('built', 8 + n_orig, 'pages')
