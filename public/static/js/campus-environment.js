/**
 * CampusCare — A Living Window into the Campus
 * Dynamic Time Engine, Natural Sky Gradients, Architectural Parallax, and Live Clock.
 */

(function () {
  'use strict';

  let currentEnvironment = 'auto'; // 'auto' | 'sunrise' | 'morning' | 'afternoon' | 'sunset' | 'night'
  let clockInterval = null;
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  document.addEventListener('DOMContentLoaded', () => {
    initTimeEnvironment();
    initStarfield();
    initMicroParallax();
  });

  /* --------------------------------------------------------------------------
     1. TIME-OF-DAY ENGINE & GREETING PHASES
     -------------------------------------------------------------------------- */
  const PHASE_CONFIG = {
    sunrise: {
      name: 'Sunrise Campus',
      icon: '🌅',
      greeting: 'Good morning — campus is waking up.'
    },
    morning: {
      name: 'Morning Campus',
      icon: '☀️',
      greeting: 'Good morning — campus is coming alive.'
    },
    afternoon: {
      name: 'Afternoon Campus',
      icon: '🌤️',
      greeting: 'Good afternoon — campus is active.'
    },
    sunset: {
      name: 'Evening Campus',
      icon: '🌇',
      greeting: 'Good evening — campus is winding down.'
    },
    night: {
      name: 'Night Campus',
      icon: '🌙',
      greeting: 'Campus is quiet, but your voice is still heard.'
    }
  };

  function detectPhase(hour) {
    if (hour >= 5 && hour < 7) {
      return 'sunrise';
    } else if (hour >= 7 && hour < 12) {
      return 'morning';
    } else if (hour >= 12 && hour < 17) {
      return 'afternoon';
    } else if (hour >= 17 && hour < 19) {
      return 'sunset';
    } else {
      return 'night';
    }
  }

  function formatTime12h(date) {
    let hours = date.getHours();
    let minutes = date.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    minutes = minutes < 10 ? '0' + minutes : minutes;
    return `${hours}:${minutes} ${ampm}`;
  }

  function updateEnvironmentState() {
    const now = new Date();
    const hour = now.getHours();
    const activeEnv = currentEnvironment === 'auto' ? detectPhase(hour) : currentEnvironment;
    const config = PHASE_CONFIG[activeEnv] || PHASE_CONFIG.morning;

    // Set attributes for CSS variable cascade
    document.documentElement.setAttribute('data-env', activeEnv);
    const heroStage = document.getElementById('campusWindowHero');
    if (heroStage) {
      heroStage.setAttribute('data-env', activeEnv);
    }

    // Update Unified Time & Greeting Chip
    const timeFormatted = formatTime12h(now);
    const timeDisplay = document.getElementById('windowTimeDisplay');
    const phaseIcon = document.getElementById('windowPhaseIcon');
    const greetingDisplay = document.getElementById('windowGreetingDisplay');

    if (timeDisplay) {
      timeDisplay.textContent = `${timeFormatted} • ${config.name}`;
    }
    if (phaseIcon) {
      phaseIcon.textContent = config.icon;
    }
    if (greetingDisplay) {
      greetingDisplay.textContent = config.greeting;
    }
  }

  function initTimeEnvironment() {
    updateEnvironmentState();

    // Re-check every 30 seconds smoothly without reload
    if (clockInterval) clearInterval(clockInterval);
    clockInterval = setInterval(updateEnvironmentState, 30000);
  }

  /* --------------------------------------------------------------------------
     2. CELESTIAL STAR GENERATOR (SUBTLE & LIMITED)
     -------------------------------------------------------------------------- */
  function initStarfield() {
    const starField = document.getElementById('windowStarfield');
    if (!starField) return;

    starField.innerHTML = '';
    const starCount = 30; // Clean, non-distracting count

    for (let i = 0; i < starCount; i++) {
      const star = document.createElement('div');
      star.className = 'window-star-dot';
      const size = Math.random() * 2 + 1;
      star.style.width = `${size}px`;
      star.style.height = `${size}px`;
      star.style.top = `${Math.random() * 55}%`;
      star.style.left = `${Math.random() * 100}%`;
      star.style.animationDelay = `${(Math.random() * 4).toFixed(1)}s`;
      star.style.animationDuration = `${(Math.random() * 3 + 2.5).toFixed(1)}s`;
      starField.appendChild(star);
    }
  }

  /* --------------------------------------------------------------------------
     3. SUBTLE MULTI-PLANE MICRO-PARALLAX (NON-AGGRESSIVE)
     -------------------------------------------------------------------------- */
  function initMicroParallax() {
    if (prefersReducedMotion) return;

    const hero = document.getElementById('campusWindowHero');
    if (!hero) return;

    const layerSky = hero.querySelector('.scenic-layer-sky');
    const layerCelestial = hero.querySelector('.scenic-layer-celestial');
    const layerDistant = hero.querySelector('.scenic-layer-distant-campus');
    const layerMain = hero.querySelector('.scenic-layer-main-hall');
    const layerTrees = hero.querySelector('.scenic-layer-trees');
    const layerPath = hero.querySelector('.scenic-layer-path');
    const layerStudents = hero.querySelector('.scenic-layer-students');
    const dashboardCard = document.getElementById('dashboardWindowPerspective');

    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    let rafId = null;

    function renderParallax() {
      // Smooth lerp damping
      currentX += (targetX - currentX) * 0.05;
      currentY += (targetY - currentY) * 0.05;

      // Micro-depth offsets specified by design:
      // Sky: 2px | Clouds: 4px | Distant: 7px | Main Hall: 10px | Trees/Path: 14px
      if (layerSky) {
        layerSky.style.transform = `translate3d(${currentX * -2}px, ${currentY * -1}px, 0)`;
      }
      if (layerCelestial) {
        layerCelestial.style.transform = `translate3d(${currentX * -4}px, ${currentY * -2}px, 0)`;
      }
      if (layerDistant) {
        layerDistant.style.transform = `translate3d(${currentX * -7}px, ${currentY * -3}px, 0)`;
      }
      if (layerMain) {
        layerMain.style.transform = `translate3d(${currentX * -10}px, ${currentY * -4}px, 0)`;
      }
      if (layerTrees) {
        layerTrees.style.transform = `translate3d(${currentX * -12}px, ${currentY * -5}px, 0)`;
      }
      if (layerPath) {
        layerPath.style.transform = `translate3d(${currentX * -14}px, ${currentY * -6}px, 0)`;
      }
      if (layerStudents) {
        layerStudents.style.transform = `translate3d(${currentX * -16}px, ${currentY * -7}px, 0)`;
      }

      // Very subtle card float
      if (dashboardCard && window.innerWidth >= 992) {
        dashboardCard.style.transform = `translate3d(${currentX * 4}px, ${currentY * 4}px, 0)`;
      }

      if (Math.abs(targetX - currentX) > 0.001 || Math.abs(targetY - currentY) > 0.001) {
        rafId = requestAnimationFrame(renderParallax);
      } else {
        rafId = null;
      }
    }

    hero.addEventListener('mousemove', (e) => {
      const rect = hero.getBoundingClientRect();
      const normX = (e.clientX - rect.left - rect.width / 2) / (rect.width / 2);
      const normY = (e.clientY - rect.top - rect.height / 2) / (rect.height / 2);

      targetX = Math.max(-1, Math.min(1, normX));
      targetY = Math.max(-1, Math.min(1, normY));

      if (!rafId) {
        rafId = requestAnimationFrame(renderParallax);
      }
    }, { passive: true });

    hero.addEventListener('mouseleave', () => {
      targetX = 0;
      targetY = 0;
      if (!rafId) {
        rafId = requestAnimationFrame(renderParallax);
      }
    }, { passive: true });
  }

  /* --------------------------------------------------------------------------
     4. DEVELOPER TEST HOOK (CONSOLE CONTROL)
     -------------------------------------------------------------------------- */
  window.setCampusEnvironment = function (mode) {
    if (['sunrise', 'morning', 'afternoon', 'sunset', 'night'].includes(mode)) {
      currentEnvironment = mode;
      updateEnvironmentState();
      console.log(`[CampusCare] Switched environment to: ${mode.toUpperCase()}`);
    } else if (mode === 'auto') {
      currentEnvironment = 'auto';
      updateEnvironmentState();
      console.log('[CampusCare] Switched environment to: AUTO (Local Time)');
    } else {
      console.warn('[CampusCare] Usage: window.setCampusEnvironment("sunrise" | "morning" | "afternoon" | "sunset" | "night" | "auto")');
    }
  };

})();
