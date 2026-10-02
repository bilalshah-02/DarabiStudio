document.addEventListener('DOMContentLoaded', () => {
  document.body.classList.add('page-loaded');

  // Scroll-reveal
  const revealEls = document.querySelectorAll('.reveal');
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  revealEls.forEach(el => io.observe(el));

  // Header shrink on scroll
  const header = document.querySelector('.site-header');
  if (header) {
    let lastY = window.scrollY;
    window.addEventListener('scroll', () => {
      header.classList.toggle('scrolled', window.scrollY > 20);
      lastY = window.scrollY;
    }, { passive: true });
  }

  // Mobile nav toggle with overlay
  const toggle = document.getElementById('menuToggle');
  const mobileNav = document.getElementById('mobileNav');
  const overlay = document.getElementById('mobileNavOverlay');
  const closeMobileNav = () => {
    toggle && toggle.classList.remove('open');
    mobileNav && mobileNav.classList.remove('open');
    overlay && overlay.classList.remove('open');
    document.body.style.overflow = '';
  };
  if (toggle && mobileNav) {
    toggle.addEventListener('click', () => {
      const isOpen = mobileNav.classList.toggle('open');
      toggle.classList.toggle('open', isOpen);
      overlay && overlay.classList.toggle('open', isOpen);
      document.body.style.overflow = isOpen ? 'hidden' : '';
    });
    mobileNav.querySelectorAll('a').forEach(a => a.addEventListener('click', closeMobileNav));
    overlay && overlay.addEventListener('click', closeMobileNav);
  }

  // Product gallery — cross-fade thumbnail switcher
  document.querySelectorAll('.pd-thumbs button').forEach(btn => {
    btn.addEventListener('click', () => {
      const mainWrap = document.querySelector('.pd-gallery-main');
      const mainImg = mainWrap ? mainWrap.querySelector('img') : null;
      if (mainImg && mainWrap) {
        mainWrap.classList.add('fading');
        setTimeout(() => {
          mainImg.src = btn.dataset.full;
          mainWrap.classList.remove('fading');
        }, 180);
      }
      document.querySelectorAll('.pd-thumbs button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  // Quantity steppers (product detail + cart)
  document.querySelectorAll('.qty-stepper').forEach(stepper => {
    const input = stepper.querySelector('input');
    const dec = stepper.querySelector('[data-step="-1"]');
    const inc = stepper.querySelector('[data-step="1"]');
    const max = parseInt(input.max || '999', 10);
    const clamp = (v) => Math.max(1, Math.min(max, v));
    dec && dec.addEventListener('click', () => { input.value = clamp((parseInt(input.value, 10) || 1) - 1); });
    inc && inc.addEventListener('click', () => { input.value = clamp((parseInt(input.value, 10) || 1) + 1); });
  });

  // Animated dial second hand
  const hourHand = document.getElementById('dial-hour'); const minHand = document.getElementById('dial-min'); const secHand = document.getElementById('dial-sec');
  if (hourHand && minHand && secHand) {
    const updateClock = () => {
      const now = new Date();
      const hours = now.getHours() % 12;
      const minutes = now.getMinutes();
      const seconds = now.getSeconds();
      secHand.setAttribute('transform', `rotate(${seconds * 6} 200 200)`);
      minHand.setAttribute('transform', `rotate(${minutes * 6 + seconds * 0.1} 200 200)`);
      hourHand.setAttribute('transform', `rotate(${hours * 30 + minutes * 0.5} 200 200)`);
    };
    updateClock();
    setInterval(updateClock, 1000);
  }
});
