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
    return s.replace('{R}', R).replace('@/', CDN + '/').replace('@%2F', CDN + '%2F')


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
%s<script>document.documentElement.className += ' js';</script>
<link rel="stylesheet" href="{R}css/site.css">
</head>
<body id="top" data-chapters="%s">

%s

%s

%s

%s<main>
%s</main>

%s

%s
%s
<script src="{R}js/site.js"></script>
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

# ---------------------------------------------------------------- residences
units = json.loads(read('data/units.json'))
status = units['status']
apts = sorted(units['apartments'], key=lambda a: int(a['slug']))
floor_img = {}
for f in units['floors']:
    key = '20' if f['slug'] == 'penthouse' else f['slug']
    if f['imgs']:
        floor_img[key] = f['imgs'][0]['src']

SECTIONS = [  # name, anchor, veil top %, veil height %, floors label
    ('The Penthouse', 'the-penthouse', 11.8, 5.9, 'Floor 20'),
    ('Crown Residences', 'crown-residences', 17.7, 14.0, 'Floors 16 to 19'),
    ('Double-Height Villas', 'double-height-villas', 31.7, 27.6, 'Floors 8 to 15'),
    ('Urban Residences', 'urban-residences', 59.3, 6.9, 'Floors 6 to 7'),
    ('Garden Terraces', 'garden-terraces', 66.2, 2.9, 'Floor 5'),
]


def available(a):
    return status.get(a['slug']) != 'Unavailable'


def outdoor(a):
    if 'terrace area' in a:
        return 'Terrace', a['terrace area']
    return 'Balcony', a.get('balcony area', '')


sel = ['  <a class="back" href="{R}index.html#the-residences"><svg viewBox="0 0 40 59" style="transform:scaleX(-1)"><use href="#chev"/></svg>Back</a>',
       '  <section class="pick">', '    <div class="tower-stage-wrap"><div class="stage">',
       '      <img src="%s/6a61fe0e07bd3dfc7ac9c471_building-img.avif" alt="Journalist House – choose a section of the building">' % CDN,
       '      <div class="veil-link" style="top:69.1%;height:30.9%;pointer-events:none"></div>']
for name, anchor, top, h, _ in SECTIONS:
    sel.append('      <a class="veil-link" href="#%s" data-name="%s" style="top:%s%%;height:%s%%" aria-label="%s"></a>' % (anchor, name, top, h, name))
sel += ['    </div></div>',
        '    <div class="pick-side"><svg viewBox="0 0 40 59"><use href="#chev"/></svg><div class="pick-text" id="pickText">Select<br>the section</div></div>',
        '  </section>']
for name, anchor, _, _, label in reversed(SECTIONS):
    mine = [a for a in apts if a['section'] == name]
    sel.append('  <section class="sect" id="%s">' % anchor)
    sel.append('    <div class="sect-head"><h2 class="h2 rv">%s</h2><span>%s</span></div>' % (name, label))
    for fl in sorted({int(a['floor']) for a in mine}):
        rows = []
        for a in [x for x in mine if int(x['floor']) == fl]:
            kind, area = outdoor(a)
            cells = [a['residence'], a.get('orientation', '—'), a['apartment area'] + ' sqm', (area + ' sqm ' + kind.lower()) if area else '—']
            if available(a):
                href = '{R}apartments/%s.html' % a['slug']
                tds = ''.join('<td%s><a href="%s">%s</a></td>' % (' class="hide-m"' if i == 1 else '', href, c) for i, c in enumerate(cells))
                rows.append('<tr>%s<td class="go"><a href="%s">View %s</a></td></tr>' % (tds, href, CHEV))
            else:
                tds = ''.join('<td%s><span>%s</span></td>' % (' class="hide-m"' if i == 1 else '', c) for i, c in enumerate(cells))
                rows.append('<tr class="na">%s<td class="go"><span>Unavailable</span></td></tr>' % tds)
        title = 'The Penthouse' if fl == 20 else 'Floor %d' % fl
        img = floor_img.get(str(fl), '')
        sel.append('    <div class="floor" id="floor-%d">' % fl)
        sel.append('      <div class="floor-img">%s</div>' % ('<img class="rv" loading="lazy" src="%s" alt="%s plan">' % (img, title) if img else ''))
        sel.append('      <div><h3>%s</h3><table class="units"><thead><tr><th>Residence</th><th class="hide-m">Orientation</th><th>Apartment</th><th>Outdoor</th><th></th></tr></thead><tbody>%s</tbody></table></div>' % (title, ''.join(rows)))
        sel.append('    </div>')
    sel.append('  </section>')
sel.append('  <div class="gcta"><a class="tlink" href="{R}see-the-residences.html"><div class="tlink-text">Residences<br>Gallery</div>%s</a></div>' % CHEV)
page('select-a-residence.html', 'Select a Residence | Tel Aviv Luxury Apartments',
     'Choose a section, floor and residence at Journalist House, Tel Aviv.', '\n'.join(sel) + '\n')

for i, a in enumerate(apts):
    kind, area = outdoor(a)
    ok = available(a) and a['plan'] and 'placeholder' not in a['plan']
    prev_a = apts[i - 1] if i > 0 else None
    next_a = apts[i + 1] if i < len(apts) - 1 else None
    fl = int(a['floor'])
    pdf = a['pdf'] if a['pdf'] and a['pdf'] != '#' else ''
    m = ['  <section class="unit">', '    <div class="unit-panel">',
         '      <div><div class="unit-k">Residence</div><div class="unit-v">%s</div></div>' % a['residence'],
         '      <div><div class="unit-k">Section</div><div class="unit-v">%s</div></div>' % a['section'],
         '      <div class="unit-two"><div><div class="unit-k">Floor</div><div class="unit-v">%s</div></div>%s</div>'
         % (a['floor'], '<div><div class="unit-k">Orientation</div><div class="unit-v">%s</div></div>' % a['orientation'] if a.get('orientation') else ''),
         '      <div class="unit-two"><div><div class="unit-k">Apartment<br>Area</div><div class="unit-v">%s<small>sqm</small></div></div>%s</div>'
         % (a['apartment area'], '<div><div class="unit-k">%s<br>Area</div><div class="unit-v">%s<small>sqm</small></div></div>' % (kind, area) if area else ''),
         '      <div class="unit-links">',
         '        ' + ('<a href="%s" target="_blank" rel="noopener">Download PDF</a>' % pdf if pdf else '<span class="off">Download PDF</span>'),
         '        ' + ('<a class="prev" href="%s.html">Prev %s</a>' % (prev_a['slug'], CHEV) if prev_a else '<span class="off">Prev</span>'),
         '        <button type="button" data-inquire data-unit="%s">Inquire</button>' % a['residence'],
         '        ' + ('<a href="%s.html">Next %s</a>' % (next_a['slug'], CHEV) if next_a else '<span class="off">Next</span>'),
         '      </div>', '    </div>', '    <div class="unit-plan">']
    if ok:
        m += ['      <div class="plan-frame"><img id="planImg" src="%s" alt="Plan of residence %s"></div>' % (a['plan'], a['residence']),
              '      <div class="plan-ctl"><button type="button" id="planOut" aria-label="Zoom out">−</button><button type="button" id="planLevel">100%</button><button type="button" id="planIn" aria-label="Zoom in">+</button></div>']
    else:
        m += ['      <div class="plan-na">This residence is<br>currently unavailable</div>']
    m += ['      <div class="disclaimer">%s</div>' % html.escape(a['disclaimer']), '    </div>', '  </section>',
          '  <div class="unit-back"><a class="back" style="padding:0" href="{R}select-a-residence.html#floor-%d"><svg viewBox="0 0 40 59" style="transform:scaleX(-1)"><use href="#chev"/></svg>Back</a></div>' % fl]
    page('apartments/%s.html' % a['slug'], a['title'], a['desc'], '\n'.join(m) + '\n')

write('css/site.css', CSS)
write('js/site.js', read('src/site.js'))
write('.nojekyll', '')
print('built', 8 + len(apts), 'pages')
