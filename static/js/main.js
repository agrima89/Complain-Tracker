/**
 * CampusCare - Student Grievance Portal
 * Global Client Utilities & Modern SaaS Interactive Features
 */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initMobileNav();
  initPasswordToggles();
  initCharCounters();
  initModals();
  initFlashToasts();

  // Landing Page SaaS Enhancements
  initHeroParticles();
  initJourneyTimelineAnimation();
  initCountUpStats();
  initPipelineIllumination();

  // Student Dashboard SaaS Enhancements
  initStudentSidebar();
  initNotificationDropdown();

  // Auth Page SaaS Enhancements
  initAuthInteractions();
});

/* ---------------- 1. THEME TOGGLE SYSTEM ---------------- */
function initThemeToggle() {
  const toggleBtns = document.querySelectorAll('#themeToggle, #authThemeToggle');
  const toggleIcons = document.querySelectorAll('#themeToggleIcon, #authThemeToggleIcon');

  function getActiveTheme() {
    return document.documentElement.getAttribute('data-theme') || localStorage.getItem('campuscare_theme') || 'dark';
  }

  function updateToggleUI(theme) {
    const isDark = theme === 'dark';
    toggleIcons.forEach((icon) => {
      icon.textContent = isDark ? '☀️' : '🌙';
    });
    const label = isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode';
    toggleBtns.forEach((btn) => {
      btn.setAttribute('title', label);
      btn.setAttribute('aria-label', label);
      btn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
    });
  }

  function setTheme(theme, savePreference = true) {
    document.documentElement.setAttribute('data-theme', theme);
    if (document.body) {
      document.body.setAttribute('data-theme', theme);
    }
    if (savePreference) {
      try {
        localStorage.setItem('campuscare_theme', theme);
      } catch (e) {
        console.warn('localStorage is unavailable', e);
      }
    }
    updateToggleUI(theme);
    // Dispatch custom event for theme-aware dynamic components
    window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
  }

  // Initial UI sync
  const currentTheme = getActiveTheme();
  setTheme(currentTheme, false);

  toggleBtns.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const activeTheme = getActiveTheme();
      const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
      setTheme(newTheme, true);
    });
  });

  // Listen to OS system color scheme changes when user hasn't explicitly set preference
  try {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', (e) => {
      const saved = localStorage.getItem('campuscare_theme');
      if (!saved) {
        setTheme(e.matches ? 'dark' : 'light', false);
      }
    });
  } catch (e) {}
}

/* ---------------- AUTH FORM SUBMIT & FORGOT PASSWORD ---------------- */
const CU_EMAIL_REGEX = /^[A-Za-z0-9]+@culkomail\.in$/i;
const CU_EMAIL_ERROR = "Please use your official Chandigarh University email (@culkomail.in)";

function validateCUEmailInput(emailInput, isSubmittingOrBlur = false) {
  if (!emailInput) return true;
  const val = emailInput.value.trim();
  if (!val) {
    emailInput.setCustomValidity('');
    return true;
  }
  const isValid = CU_EMAIL_REGEX.test(val);
  if (isValid) {
    emailInput.setCustomValidity('');
    return true;
  } else if (isSubmittingOrBlur) {
    emailInput.setCustomValidity(CU_EMAIL_ERROR);
    return false;
  } else {
    emailInput.setCustomValidity('');
    return false;
  }
}

function initAuthInteractions() {
  const loginForm = document.getElementById('studentLoginForm');
  const registerForm = document.querySelector('form[action*="register"]');
  const submitBtn = document.getElementById('authSubmitBtn');
  const forgotLink = document.getElementById('forgotPasswordLink');

  [loginForm, registerForm].forEach((form) => {
    if (!form) return;
    const emailInput = form.querySelector('#email, input[name="email"]');
    if (emailInput) {
      emailInput.addEventListener('input', () => {
        validateCUEmailInput(emailInput, false);
      });
      emailInput.addEventListener('blur', () => {
        if (emailInput.value.trim() && !validateCUEmailInput(emailInput, true)) {
          showToast('error', 'Invalid Email', CU_EMAIL_ERROR);
        }
      });
    }

    form.addEventListener('submit', (e) => {
      if (emailInput && !validateCUEmailInput(emailInput, true)) {
        e.preventDefault();
        emailInput.reportValidity();
        showToast('error', 'Invalid Email Address', CU_EMAIL_ERROR);
        emailInput.focus();
        if (submitBtn) {
          submitBtn.classList.remove('is-submitting');
          submitBtn.innerHTML = '<span class="btn-auth-text">Sign In</span> <span class="btn-auth-arrow">→</span>';
        }
        return;
      }

      if (form === loginForm && submitBtn) {
        const passInput = loginForm.querySelector('#password');
        if (emailInput && passInput && emailInput.value && passInput.value) {
          submitBtn.classList.add('is-submitting');
          submitBtn.innerHTML = '<span class="auth-spinner"></span> <span>Signing in...</span>';
        }
      }
    });
  });

  if (forgotLink) {
    forgotLink.addEventListener('click', (e) => {
      e.preventDefault();
      showToast(
        'info',
        'Password Reset Help',
        'Please contact the Dean of Student Welfare office or Campus IT Helpdesk to verify your credentials and reset your password.',
        6000
      );
    });
  }
}

/* ---------------- 2. TOAST NOTIFICATION SYSTEM ---------------- */
function getToastContainer() {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  return container;
}

function showToast(type = 'info', title = '', message = '', duration = 4000) {
  const container = getToastContainer();
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const iconMap = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };

  toast.innerHTML = `
    <div class="toast-icon">${iconMap[type] || 'ℹ'}</div>
    <div class="toast-content">
      ${title ? `<div class="toast-title">${title}</div>` : ''}
      <div class="toast-message">${message}</div>
    </div>
    <button type="button" class="toast-close" aria-label="Close">&times;</button>
  `;

  const closeBtn = toast.querySelector('.toast-close');
  closeBtn.addEventListener('click', () => dismissToast(toast));

  container.appendChild(toast);

  if (duration > 0) {
    setTimeout(() => dismissToast(toast), duration);
  }
}

function dismissToast(toast) {
  toast.style.opacity = '0';
  toast.style.transform = 'translateX(100%)';
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 200);
}

function initFlashToasts() {
  const flashElements = document.querySelectorAll('.server-flash-msg');
  flashElements.forEach((el) => {
    const type = el.dataset.type || 'info';
    const title = el.dataset.title || '';
    const message = el.innerText.trim();
    if (message) {
      showToast(type, title, message);
    }
    el.remove();
  });
}

/* ---------------- 3. MOBILE NAVIGATION TOGGLE ---------------- */
function initMobileNav() {
  const toggleBtn = document.querySelector('.mobile-nav-toggle');
  const navMenu = document.querySelector('.navbar-nav');

  if (toggleBtn && navMenu) {
    toggleBtn.addEventListener('click', () => {
      navMenu.classList.toggle('is-open');
      const isOpen = navMenu.classList.contains('is-open');
      toggleBtn.setAttribute('aria-expanded', isOpen);
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
      if (!navMenu.contains(e.target) && !toggleBtn.contains(e.target) && navMenu.classList.contains('is-open')) {
        navMenu.classList.remove('is-open');
        toggleBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }
}

/* ---------------- 4. PASSWORD VISIBILITY TOGGLE ---------------- */
function initPasswordToggles() {
  document.querySelectorAll('.password-toggle-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const input = btn.closest('.input-password-wrapper')?.querySelector('input');
      if (input) {
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        btn.textContent = isPassword ? '🙈' : '👁️';
        btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
      }
    });
  });
}

/* ---------------- 5. CHARACTER COUNTER ---------------- */
function initCharCounters() {
  document.querySelectorAll('[data-char-count]').forEach((textarea) => {
    const max = textarea.getAttribute('maxlength') || textarea.dataset.charCount;
    const targetId = textarea.dataset.counterTarget;
    const counterEl = targetId ? document.getElementById(targetId) : textarea.parentNode.querySelector('.char-counter');

    const updateCount = () => {
      const current = textarea.value.length;
      if (counterEl) {
        counterEl.textContent = `${current} / ${max}`;
      }
    };

    textarea.addEventListener('input', updateCount);
    updateCount();
  });
}

/* ---------------- 6. ACCESSIBLE MODALS ---------------- */
function initModals() {
  document.querySelectorAll('[data-modal-target]').forEach((trigger) => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const modalId = trigger.dataset.modalTarget;
      openModal(modalId);
    });
  });

  document.querySelectorAll('.modal-backdrop').forEach((backdrop) => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop || e.target.closest('[data-modal-close]')) {
        closeModal(backdrop.id);
      }
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const openModalEl = document.querySelector('.modal-backdrop.is-open');
      if (openModalEl) closeModal(openModalEl.id);
    }
  });
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('is-open');
    document.body.style.overflow = '';
  }
}

/* --------------------------------------------------------------------------
   7. HERO AMBIENT PARTICLES & LIGHT TRAILS (ELEGANT, BATTERY-EFFICIENT)
   -------------------------------------------------------------------------- */
function initHeroParticles() {
  const canvas = document.getElementById('heroParticleCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let animationFrameId = null;
  let isVisible = true;

  let width = (canvas.width = canvas.parentElement.offsetWidth || window.innerWidth);
  let height = (canvas.height = canvas.parentElement.offsetHeight || 600);

  function handleResize() {
    if (!canvas.parentElement) return;
    width = canvas.width = canvas.parentElement.offsetWidth;
    height = canvas.height = canvas.parentElement.offsetHeight;
    createParticles();
  }

  window.addEventListener('resize', handleResize);

  // Pause when off-screen to preserve performance
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      isVisible = entry.isIntersecting;
      if (isVisible && !animationFrameId) {
        animate();
      }
    });
  }, { threshold: 0.05 });

  observer.observe(canvas);

  const particleCount = Math.min(Math.floor(width / 32), 45);
  let particles = [];

  function getParticleColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      dot: isDark ? 'rgba(96, 165, 250, ' : 'rgba(37, 99, 235, ',
      trail: isDark ? 'rgba(59, 130, 246, ' : 'rgba(59, 130, 246, '
    };
  }

  function createParticles() {
    particles = [];
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        radius: Math.random() * 1.8 + 0.8,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        alpha: Math.random() * 0.45 + 0.15,
        phase: Math.random() * Math.PI * 2
      });
    }
  }

  createParticles();

  function animate() {
    if (!isVisible) {
      animationFrameId = null;
      return;
    }

    ctx.clearRect(0, 0, width, height);
    const colors = getParticleColors();

    // Update and draw particles
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.phase += 0.015;

      // Wrap around edges gracefully
      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      const dynamicAlpha = p.alpha * (0.7 + 0.3 * Math.sin(p.phase));

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = `${colors.dot}${dynamicAlpha})`;
      ctx.fill();

      // Draw delicate connecting light trails between close particles
      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dx = p.x - p2.x;
        const dy = p.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 110) {
          const lineAlpha = (1 - dist / 110) * 0.18;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `${colors.trail}${lineAlpha})`;
          ctx.lineWidth = 0.75;
          ctx.stroke();
        }
      }
    }

    animationFrameId = requestAnimationFrame(animate);
  }

  animate();

  window.addEventListener('themeChanged', () => {
    // Redraw on next frame with updated theme colors
  });
}

/* --------------------------------------------------------------------------
   8. COMPLAINT JOURNEY TIMELINE SEQUENTIAL ANIMATION
   -------------------------------------------------------------------------- */
function initJourneyTimelineAnimation() {
  const timeline = document.getElementById('journeyTimeline');
  const progressFill = document.getElementById('journeyProgressFill');
  if (!timeline) return;

  const nodes = timeline.querySelectorAll('.timeline-node');

  // Sequential illumination on initial view
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        // Animate progress bar fill to 75%
        if (progressFill) {
          setTimeout(() => {
            progressFill.style.width = '75%';
          }, 300);
        }

        // Animate nodes sequentially
        nodes.forEach((node, idx) => {
          setTimeout(() => {
            node.classList.add('step-glow-flash');
            setTimeout(() => node.classList.remove('step-glow-flash'), 800);
          }, 400 + idx * 320);
        });

        observer.unobserve(timeline);
      }
    });
  }, { threshold: 0.2 });

  observer.observe(timeline);
}

/* --------------------------------------------------------------------------
   9. LIVE STATISTICS COUNT-UP NUMBERS (INTERSECTION OBSERVER)
   -------------------------------------------------------------------------- */
function initCountUpStats() {
  const statSection = document.getElementById('statsSection');
  if (!statSection) return;

  const counters = statSection.querySelectorAll('.metric-counter');

  function animateCounter(el) {
    const target = parseFloat(el.dataset.target || 0);
    const decimals = parseInt(el.dataset.decimals || 0, 10);
    const prefix = el.dataset.prefix || '';
    const suffix = el.dataset.suffix || '';
    const duration = 1800; // ms
    const startTime = performance.now();

    function updateValue(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Smooth cubic ease-out
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const current = progress === 1 ? target : easeOut * target;

      if (decimals > 0) {
        el.textContent = `${prefix}${current.toFixed(decimals)}${suffix}`;
      } else {
        el.textContent = `${prefix}${Math.floor(current).toLocaleString()}${suffix}`;
      }

      if (progress < 1) {
        requestAnimationFrame(updateValue);
      }
    }

    requestAnimationFrame(updateValue);
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        counters.forEach((counter) => animateCounter(counter));
        observer.unobserve(statSection);
      }
    });
  }, { threshold: 0.25 });

  observer.observe(statSection);
}

/* --------------------------------------------------------------------------
   10. HOW CAMPUSCARE WORKS - SCROLL-ACTIVATED CONNECTING LINE
   -------------------------------------------------------------------------- */
function initPipelineIllumination() {
  const section = document.getElementById('howItWorksSection');
  const trackFill = document.getElementById('pipelineTrackFill');
  if (!section || !trackFill) return;

  trackFill.style.width = '0%';

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        trackFill.style.width = '100%';
        observer.unobserve(section);
      }
    });
  }, { threshold: 0.3 });

  observer.observe(section);
}

/* --------------------------------------------------------------------------
   11. STUDENT DASHBOARD SIDEBAR (RESPONSIVE DRAWER & BACKDROP)
   -------------------------------------------------------------------------- */
function initStudentSidebar() {
  const toggleBtn = document.getElementById('sidebarMobileToggle');
  const sidebar = document.getElementById('studentSidebar');
  const overlay = document.getElementById('sidebarOverlay');

  if (!sidebar) return;

  function openSidebar() {
    sidebar.classList.add('is-open');
    if (overlay) overlay.classList.add('is-active');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar.classList.remove('is-open');
    if (overlay) overlay.classList.remove('is-active');
    document.body.style.overflow = '';
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (sidebar.classList.contains('is-open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (overlay) {
    overlay.addEventListener('click', closeSidebar);
  }

  // Close when clicking nav links on mobile
  const navLinks = sidebar.querySelectorAll('.sidebar-nav-link, .sidebar-logout-btn');
  navLinks.forEach((link) => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 1024) {
        closeSidebar();
      }
    });
  });

  // Handle window resize
  window.addEventListener('resize', () => {
    if (window.innerWidth > 1024 && sidebar.classList.contains('is-open')) {
      closeSidebar();
    }
  });
}

/* --------------------------------------------------------------------------
   12. NOTIFICATION BELL DROPDOWNS (STUDENT & PUBLIC)
   -------------------------------------------------------------------------- */
function initNotificationDropdown() {
  const triggers = [
    { btn: document.getElementById('notificationBellBtn'), menu: document.getElementById('notificationDropdown') },
    { btn: document.getElementById('publicNotificationBtn'), menu: document.getElementById('publicNotificationDropdown') }
  ];

  triggers.forEach(({ btn, menu }) => {
    if (!btn || !menu) return;

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isVisible = menu.style.display === 'block';
      // Close all first
      triggers.forEach(t => { if (t.menu) t.menu.style.display = 'none'; });
      menu.style.display = isVisible ? 'none' : 'block';
    });

    document.addEventListener('click', (e) => {
      if (!menu.contains(e.target) && e.target !== btn && !btn.contains(e.target)) {
        menu.style.display = 'none';
      }
    });
  });
}


