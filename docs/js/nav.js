// BrainBench - Dynamic Navigation Bar + Shared Animation Utilities

// ===== NAVIGATION =====
function initNav(activePage) {
  const pages = [
    { id: 'index', label: 'Dashboard', href: 'index.html' },
    { id: 'models', label: 'Models', href: 'models.html' },
    { id: 'datasets', label: 'Datasets', href: 'datasets.html' },
    { id: 'methodology', label: 'Methodology', href: 'methodology.html' },
    { id: 'about', label: 'About', href: 'about.html' },
  ];

  const nav = document.getElementById('nav');
  if (!nav) return;

  const links = pages.map(p => {
    const isActive = p.id === activePage;
    const cls = isActive
      ? 'nav-link nav-link-active text-blue-400'
      : 'nav-link text-gray-400 hover:text-white';
    return `<a href="${p.href}" class="${cls} pb-1 text-sm font-medium transition-colors">${p.label}</a>`;
  }).join('');

  const mobileLinks = pages.map(p => {
    const isActive = p.id === activePage;
    const cls = isActive
      ? 'text-blue-400 bg-slate-700/50'
      : 'text-gray-400 hover:text-white hover:bg-slate-700/50';
    return `<a href="${p.href}" class="${cls} block px-4 py-2.5 rounded-lg text-sm font-medium transition-colors">${p.label}</a>`;
  }).join('');

  nav.innerHTML = `
    <nav class="fixed top-0 left-0 right-0 z-50 bg-slate-900/80 backdrop-blur-xl border-b border-slate-700/30">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <a href="index.html" class="flex items-center gap-3 group">
            <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/30 transition-shadow">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
            </div>
            <span class="text-white font-bold text-lg tracking-tight">BrainBench</span>
          </a>
          <div class="hidden md:flex items-center gap-6">${links}</div>
          <button id="mobile-menu-btn" class="md:hidden text-gray-400 hover:text-white transition-colors" onclick="toggleMobileMenu()">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </button>
        </div>
      </div>
      <div id="mobile-menu" class="hidden md:hidden border-t border-slate-700/30 bg-slate-900/95 backdrop-blur-xl p-3 space-y-1">
        ${mobileLinks}
      </div>
    </nav>
  `;
}

function toggleMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  if (menu) menu.classList.toggle('hidden');
}

// ===== FOOTER =====
function initFooter() {
  const footer = document.getElementById('footer');
  if (!footer) return;
  footer.innerHTML = `
    <footer class="border-t border-slate-700/30 bg-slate-900/80 backdrop-blur-sm mt-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="flex flex-col md:flex-row items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <div class="w-6 h-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded flex items-center justify-center">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
            </div>
            <span class="text-gray-500 text-sm">BrainBench &mdash; Florida Institute of Technology &mdash; Senior Design 2026</span>
          </div>
          <div class="text-gray-600 text-sm">Orion Powers &amp; Daniella Seum</div>
        </div>
      </div>
    </footer>
  `;
}

// ===== SCROLL REVEAL (IntersectionObserver) =====
function initScrollReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.08,
    rootMargin: '0px 0px -40px 0px'
  });

  document.querySelectorAll('.scroll-reveal').forEach(el => observer.observe(el));
}

// ===== ANIMATED NUMBER COUNTERS =====
function initCounters() {
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseFloat(el.dataset.count);
        const suffix = el.dataset.suffix || '';
        const decimals = el.dataset.decimals ? parseInt(el.dataset.decimals) : 0;
        const duration = parseInt(el.dataset.duration || '1400');
        const useCommas = el.dataset.commas !== 'false';
        animateNumber(el, target, suffix, decimals, duration, useCommas);
        counterObserver.unobserve(el);
      }
    });
  }, { threshold: 0.3 });

  document.querySelectorAll('[data-count]').forEach(el => counterObserver.observe(el));
}

function animateNumber(el, target, suffix, decimals, duration, useCommas) {
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // ease-out cubic
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = eased * target;

    let display;
    if (decimals > 0) {
      display = current.toFixed(decimals);
    } else {
      display = Math.floor(current);
      if (useCommas) display = display.toLocaleString();
    }

    el.textContent = display + suffix;

    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      let final = decimals > 0 ? target.toFixed(decimals) : target;
      if (decimals === 0 && useCommas) final = target.toLocaleString();
      el.textContent = final + suffix;
    }
  }

  requestAnimationFrame(update);
}

// ===== PROGRESS BAR ANIMATION =====
function initProgressBars() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const bars = entry.target.querySelectorAll('.progress-fill');
        bars.forEach((bar, i) => {
          setTimeout(() => {
            bar.style.width = bar.dataset.width;
            bar.classList.add('animate');
          }, i * 150);
        });
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('.progress-group').forEach(el => observer.observe(el));
}

// ===== MOUSE SPOTLIGHT =====
function initSpotlight() {
  document.querySelectorAll('.card-spotlight').forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      card.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
      card.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
    });
  });
}

// ===== INIT ALL ENHANCEMENTS =====
function initEnhancements() {
  initScrollReveal();
  initCounters();
  initProgressBars();
  initSpotlight();
}
