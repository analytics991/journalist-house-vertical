(function () {
  'use strict';
  /* Where the Inquire form is sent. Leave empty to fall back to an e-mail draft
     addressed to INQUIRY_EMAIL. Set it to your form handler URL (POST) to go live. */
  var FORM_ENDPOINT = '';
  var INQUIRY_EMAIL = 'info@journalist-house.com';
  var VIMEO_ID = '1237913403';

  var doc = document, body = doc.body;
  var $ = function (s, r) { return (r || doc).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || doc).querySelectorAll(s)); };
  var clamp = function (v, a, b) { return Math.max(a, Math.min(b, v)); };
  var mobile = window.matchMedia('(max-width: 767px)');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- split headings into letters for the scroll-driven ink effect ---- */
  $$('[data-chars]').forEach(function (el) {
    var words = el.textContent.trim().split(/\s+/);
    el.setAttribute('aria-label', words.join(' '));
    el.textContent = '';
    words.forEach(function (word, i) {
      var w = doc.createElement('span');
      w.className = 'w';
      w.setAttribute('aria-hidden', 'true');
      word.split('').forEach(function (c) {
        var s = doc.createElement('span');
        s.className = 'ch';
        s.textContent = c;
        w.appendChild(s);
      });
      el.appendChild(w);
      if (i < words.length - 1) { el.appendChild(doc.createTextNode(' ')); }
    });
    el._chars = $$('.ch', el);
    el._pin = el.closest('[data-pin-chars]');
  });

  /* ---- reveal on scroll ---- */
  var revealEls = $$('.rv');
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.05 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('in'); });
  }

  /* ---- scroll-driven pieces ---- */
  var plx = $$('[data-plx]');
  var charEls = $$('[data-chars]');
  var feat = $('#feat'), featLines = $$('.feat-list h2');
  var tower = $('.tower[data-pinned]'), veils = $$('.veil', tower || doc), markers = $$('.marker', tower || doc);
  var nights = $$('[data-night]'), grows = $$('[data-grow]');
  nights.forEach(function (fig) {
    fig._labels = $$('svg > g > g', fig).sort(function (a, b) {
      var la = a.querySelector('line'), lb = b.querySelector('line');
      return (la ? +la.getAttribute('x1') : 0) - (lb ? +lb.getAttribute('x1') : 0);
    });
  });
  var vidPins = $$('[data-vid-pin]');
  vidPins.forEach(function (pin) {
    var v = pin._video = $('video', pin);
    v.pause();
    v.addEventListener('loadedmetadata', onScroll);
    /* phones only load the frames once playback has been touched */
    var prime = function () {
      var p = v.play();
      if (p && p.then) { p.then(function () { v.pause(); onScroll(); }).catch(function () {}); }
      window.removeEventListener('touchstart', prime);
    };
    window.addEventListener('touchstart', prime, { passive: true });
  });
  var slidePins = $$('[data-slide-pin]');
  slidePins.forEach(function (pin) { pin._img = $('img', pin); });
  var chapters = $$('[data-chapter]');
  var chNames = (body.getAttribute('data-chapters') || '').split('|').filter(Boolean);
  var chName = $('#chName'), chFill = $('#chFill'), curChapter = -1;
  var ticking = false;

  function pinProgress(el, vh) {
    var r = el.getBoundingClientRect();
    var total = r.height - vh;
    if (total <= 0) { return 1; }
    return clamp(-r.top / total, 0, 1);
  }

  function update() {
    ticking = false;
    var vh = window.innerHeight;
    var isMobile = mobile.matches;

    if (!reduce) {
      plx.forEach(function (img) {
        var r = img.parentNode.getBoundingClientRect();
        if (r.bottom < -100 || r.top > vh + 100) { return; }
        var c = (r.top + r.height / 2 - vh / 2) / vh;
        var zoom = 1.14 - 0.14 * clamp((vh - r.top) / (vh + r.height), 0, 1);
        img.style.transform = 'translate3d(0,' + (clamp(c, -1, 1) * -7).toFixed(2) + '%,0) scale(' + zoom.toFixed(4) + ')';
      });
    }

    charEls.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.bottom < -200 || r.top > vh + 200) { return; }
      var pin = el._pin;
      var p = reduce ? 1 : (pin ? clamp((pinProgress(pin, vh) - 0.05) / 0.8, 0, 1) : clamp((vh * 0.8 - r.top) / (vh * 0.45), 0, 1));
      var n = Math.round(p * el._chars.length);
      el._chars.forEach(function (c, i) { c.classList.toggle('on', i < n); });
    });

    nights.forEach(function (fig) {
      var r = fig.getBoundingClientRect();
      if (r.bottom < -200 || r.top > vh + 200) { return; }
      var p = reduce ? 1 : clamp(pinProgress(fig, vh) / 0.85, 0, 1);
      var n = r.top > vh * 0.25 ? 0 : Math.ceil(p * fig._labels.length);
      fig._labels.forEach(function (g, i) { g.classList.toggle('on', i < n); });
    });

    grows.forEach(function (fig) {
      var r = fig.getBoundingClientRect();
      if (r.bottom < -200 || r.top > vh + 200) { return; }
      var p = (reduce || isMobile) ? 1 : clamp((vh - r.top) / (vh * 0.8), 0, 1);
      fig.firstElementChild.style.width = (38 + 62 * p).toFixed(2) + '%';
    });

    vidPins.forEach(function (pin) {
      var v = pin._video;
      if (!v || !v.duration || isNaN(v.duration)) { return; }
      var r = pin.getBoundingClientRect();
      if (r.bottom < -200 || r.top > vh + 200) { return; }
      var t = clamp(pinProgress(pin, vh) / 0.92, 0, 1) * (v.duration - 0.05);
      if (Math.abs(v.currentTime - t) > 0.03) { v.currentTime = t; }
    });

    slidePins.forEach(function (pin) {
      var r = pin.getBoundingClientRect();
      if (r.bottom < -200 || r.top > vh + 200) { return; }
      /* starts arriving a little before the section locks, and is centred well before it releases */
      var lead = clamp((vh - r.top) / vh, 0, 1) * 0.25;
      var p = reduce ? 1 : clamp(lead + pinProgress(pin, vh) / 0.7 * 0.75, 0, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      pin._img.style.transform = 'translate3d(' + ((1 - eased) * 100).toFixed(2) + 'vw,0,0)';
    });

    if (feat) {
      var fp = pinProgress(feat, vh);
      var on = Math.floor(fp * (featLines.length + 0.999));
      featLines.forEach(function (l, i) { l.classList.toggle('on', i < Math.max(on, 1)); });
    }

    if (tower) {
      var tp = isMobile ? 1 : pinProgress(tower, vh);
      var step = isMobile ? 5 : Math.floor(tp * 6.2);
      veils.forEach(function (v) { v.classList.toggle('off', +v.getAttribute('data-step') <= step); });
      markers.forEach(function (m) { m.classList.toggle('on', +m.getAttribute('data-step') <= step); });
    }

    if (chName && chNames.length) {
      var idx = 0;
      chapters.forEach(function (s) {
        if (s.getBoundingClientRect().top <= vh * 0.5) { idx = +s.getAttribute('data-chapter'); }
      });
      if (idx !== curChapter) {
        curChapter = idx;
        chName.textContent = chNames[idx] || '';
        var span = chNames.length > 1 ? (13 / 3) / (chNames.length - 1) : 0;
        chFill.style.transform = 'translateX(' + (idx * span * 100) + '%)';
      }
    }
  }
  function onScroll() {
    if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  window.addEventListener('load', onScroll);
  update();

  /* ---- chapters menu ---- */
  var menuBtn = $('#menuBtn'), menu = $('#menu');
  function setMenu(open) {
    body.classList.toggle('menu-open', open);
    body.classList.toggle('lock', open || !!$('.modal.open'));
    menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    menuBtn.setAttribute('aria-label', open ? 'Close chapters menu' : 'Open chapters menu');
    menu.setAttribute('aria-hidden', open ? 'false' : 'true');
  }
  menuBtn.addEventListener('click', function () { setMenu(!body.classList.contains('menu-open')); });
  $$('a', menu).forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });

  /* ---- overlays ---- */
  var lastFocus = null;
  function openModal(m) {
    lastFocus = doc.activeElement;
    setMenu(false);
    m.classList.add('open');
    m.setAttribute('aria-hidden', 'false');
    body.classList.add('lock');
    var f = $('input, button.x', m);
    if (f) { window.setTimeout(function () { f.focus(); }, 80); }
  }
  function closeModal(m) {
    m.classList.remove('open');
    m.setAttribute('aria-hidden', 'true');
    body.classList.remove('lock');
    if (m.id === 'video') { $('#vidFrame').innerHTML = ''; }
    if (lastFocus && lastFocus.focus) { lastFocus.focus(); }
  }
  var inquire = $('#inquire'), video = $('#video');
  $$('[data-inquire]').forEach(function (b) {
    b.addEventListener('click', function (e) {
      e.preventDefault();
      var unit = b.getAttribute('data-unit');
      if (unit) { var u = $('input[name="Residence"]', inquire); if (u) { u.value = unit; } }
      openModal(inquire);
    });
  });
  $$('[data-video]').forEach(function (b) {
    b.addEventListener('click', function () {
      $('#vidFrame').innerHTML = '<iframe src="https://player.vimeo.com/video/' + VIMEO_ID + '?autoplay=1&title=0&byline=0&portrait=0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen title="Journalist House film"></iframe>';
      openModal(video);
    });
  });
  $$('[data-close]').forEach(function (b) {
    b.addEventListener('click', function () { closeModal(b.closest('.modal')); });
  });
  doc.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') { return; }
    var m = $('.modal.open');
    if (m) { closeModal(m); } else if (body.classList.contains('menu-open')) { setMenu(false); }
  });

  /* ---- inquire forms (overlay + in-page) ---- */
  $$('form.inq-f').forEach(function (form) {
    var box = form.parentNode;
    var sel = $('select', form);
    sel.addEventListener('change', function () { sel.classList.toggle('filled', !!sel.value); });
    function note(head, text) {
      $('.inq-note b', box).textContent = head;
      $('.inq-note span', box).textContent = text;
      box.classList.add('sent');
    }
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      var data = new FormData(form);
      if (FORM_ENDPOINT) {
        fetch(FORM_ENDPOINT, { method: 'POST', body: data, headers: { 'Accept': 'application/json' } })
          .then(function (r) {
            if (!r.ok) { throw new Error('bad status'); }
            note('Thank you for your interest', 'We have received your details and will be in touch soon to provide further information.');
          })
          .catch(function () {
            note('Oops!', 'Something went wrong while submitting the form.');
          });
        return;
      }
      var lines = [
        'First name: ' + data.get('First-Name'),
        'Last name: ' + data.get('Last-Name'),
        'Email: ' + data.get('Email'),
        'Phone: ' + data.get('Phone-Number'),
        'Interested in: ' + data.get('Interested-in'),
        'Privacy Policy accepted: yes',
        'Marketing consent: yes'
      ];
      if (data.get('Residence')) { lines.splice(5, 0, 'Residence: ' + data.get('Residence')); }
      window.location.href = 'mailto:' + INQUIRY_EMAIL + '?subject=' + encodeURIComponent('Journalist House inquiry') + '&body=' + encodeURIComponent(lines.join('\n'));
      note('One more step', 'Your e-mail app has opened with your details. Press send there to complete your inquiry, or call +972-3-5040045.');
    });
  });

  /* ---- residence selector: hovering a level names it ---- */
  var pickText = $('#pickText');
  if (pickText) {
    var pickDefault = pickText.innerHTML;
    $$('.veil-link').forEach(function (a) {
      a.addEventListener('mouseenter', function () { pickText.textContent = a.getAttribute('data-name'); });
      a.addEventListener('mouseleave', function () { pickText.innerHTML = pickDefault; });
    });
  }

  /* ---- residences gallery ---- */
  var gal = $('#gal');
  if (gal) {
    var slides = $$('.gal-slide', gal), tabs = $$('.gal-tabs button', gal);
    var gPrev = $('#galPrev'), gNext = $('#galNext'), cur = 0;
    var show = function (i) {
      cur = clamp(i, 0, slides.length - 1);
      var tab = slides[cur].getAttribute('data-tab');
      slides.forEach(function (s, k) { s.classList.toggle('on', k === cur); });
      tabs.forEach(function (t) {
        var on = t.getAttribute('data-tab') === tab;
        t.classList.toggle('on', on);
        t.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      gPrev.disabled = cur === 0;
      gNext.disabled = cur === slides.length - 1;
    };
    gPrev.addEventListener('click', function () { show(cur - 1); });
    gNext.addEventListener('click', function () { show(cur + 1); });
    tabs.forEach(function (t) {
      t.addEventListener('click', function () {
        var tab = t.getAttribute('data-tab');
        for (var k = 0; k < slides.length; k++) {
          if (slides[k].getAttribute('data-tab') === tab) { show(k); break; }
        }
      });
    });
    doc.addEventListener('keydown', function (e) {
      if ($('.modal.open') || body.classList.contains('menu-open')) { return; }
      if (e.key === 'ArrowRight') { show(cur + 1); }
      if (e.key === 'ArrowLeft') { show(cur - 1); }
    });
    show(0);
  }

  /* ---- unit plan zoom ---- */
  var plan = $('#planImg');
  if (plan) {
    var z = 1, lvl = $('#planLevel');
    var setZ = function (v) {
      z = clamp(v, 1, 3);
      plan.style.width = (z * 100) + '%';
      plan.style.maxHeight = z > 1 ? 'none' : '';
      lvl.textContent = Math.round(z * 100) + '%';
    };
    $('#planIn').addEventListener('click', function () { setZ(z + 0.5); });
    $('#planOut').addEventListener('click', function () { setZ(z - 0.5); });
    lvl.addEventListener('click', function () { setZ(1); });
  }

  /* ---- loader, as on the original site: the grey logo fills with black from
     the left while the first images load, then the white screen wipes away ---- */
  var ld = $('#ld');
  if (ld && doc.documentElement.classList.contains('no-ld')) {
    ld.style.display = 'none';
  } else if (ld) {
    var fill = $('.ld-fill', ld), started = Date.now(), finished = false, prog = 0;
    var setFill = function (p, dur) {
      prog = Math.max(prog, p);
      fill.style.transitionDuration = dur + 's';
      fill.style.clipPath = 'inset(0% ' + (100 - prog * 100) + '% 0% 0%)';
    };
    var finish = function () {
      if (finished) { return; }
      finished = true;
      setFill(1, 0.35);
      window.setTimeout(function () {
        ld.classList.add('out');
        doc.documentElement.classList.remove('ld-on');
        onScroll();
        window.setTimeout(function () { ld.style.display = 'none'; }, 1200);
      }, 380);
    };
    var done = function () { window.setTimeout(finish, Math.max(0, 700 - (Date.now() - started))); };
    if (reduce) {
      ld.style.display = 'none';
      doc.documentElement.classList.remove('ld-on');
    } else {
      window.requestAnimationFrame(function () { setFill(0.1, 0.6); });
      var first = $$('img').filter(function (im) { return im.getAttribute('loading') !== 'lazy' && im.offsetParent !== null; }).slice(0, 12);
      var left = first.length, total = first.length;
      if (!total) { done(); }
      first.forEach(function (im) {
        var one = function () {
          left -= 1;
          setFill(0.1 + 0.9 * (1 - left / total), 0.5);
          if (left <= 0) { done(); }
        };
        if (im.complete) { one(); } else { im.addEventListener('load', one); im.addEventListener('error', one); }
      });
      window.setTimeout(finish, 6000);
      window.addEventListener('pageshow', function (e) {
        if (e.persisted) { ld.style.display = 'none'; doc.documentElement.classList.remove('ld-on'); }
      });
    }
  }

  /* ---- cookies ---- */
  var cookies = $('#cookies'), seen = false;
  try { seen = window.localStorage.getItem('jh-cookies') === '1'; } catch (err) { seen = false; }
  if (!seen) { cookies.classList.add('show'); }
  $('#cookieOk').addEventListener('click', function () {
    cookies.classList.remove('show');
    try { window.localStorage.setItem('jh-cookies', '1'); } catch (err) { /* private mode */ }
  });
})();
