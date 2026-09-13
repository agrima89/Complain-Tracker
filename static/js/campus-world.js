/**
 * CampusCare — Dark Cinematic Living University Campus Controller
 * Immersive real-time atmospheric lighting, continuous environmental movement,
 * multi-plane camera parallax, and box-less digital interface manager.
 */

(function () {
  'use strict';

  let currentEnvironment = 'auto'; // 'auto' | 'night' | 'sunset' | 'afternoon' | 'morning' | 'sunrise'
  let clockTimer = null;
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  document.addEventListener('DOMContentLoaded', () => {
    initWorldTimeEngine();
    initWorldStars();
    initWindowGlowCycling();
    initCinematicParallax();
    initCampusPulseLoop();
  });

  /* --------------------------------------------------------------------------
     1. TIME-OF-DAY ATMOSPHERIC ENGINE
     -------------------------------------------------------------------------- */
  const WORLD_CONFIG = {
    morning: {
      name: 'MORNING CAMPUS',
      symbol: '☀️',
      greeting: 'Good morning — campus is coming alive.'
    },
    afternoon: {
      name: 'AFTERNOON CAMPUS',
      symbol: '🌤️',
      greeting: 'Good afternoon — campus is active.'
    },
    evening: {
      name: 'EVENING CAMPUS',
      symbol: '🌇',
      greeting: 'Good evening — campus is winding down.'
    },
    night: {
      name: 'NIGHT CAMPUS',
      symbol: '☾',
      greeting: 'Campus is quiet, but your voice is still heard.'
    }
  };

  /**
   * Centralized function to evaluate the campus time category based on local browser time:
   * 🌅 MORNING:   5:00 AM – 11:59 AM (hours 5 to 11)
   * ☀️ AFTERNOON: 12:00 PM – 4:59 PM  (hours 12 to 16)
   * 🌇 EVENING:   5:00 PM – 7:59 PM  (hours 17 to 19)
   * 🌙 NIGHT:     8:00 PM – 4:59 AM  (hours 20 to 23, 0 to 4)
   * @param {Date} [dateObj]
   * @returns {'morning' | 'afternoon' | 'evening' | 'night'}
   */
  function getCampusBackground(dateObj) {
    const now = dateObj || new Date();
    const hour = now.getHours(); // 0 - 23 in user's local timezone

    if (hour >= 5 && hour < 12) {
      return 'morning';
    } else if (hour >= 12 && hour < 17) {
      return 'afternoon';
    } else if (hour >= 17 && hour < 20) {
      return 'evening';
    } else {
      return 'night';
    }
  }
  window.getCampusBackground = getCampusBackground;

  function getPhaseForHour(hour) {
    const d = new Date();
    d.setHours(hour, 30, 0, 0);
    return getCampusBackground(d);
  }

  function formatTime(date) {
    let hours = date.getHours();
    let minutes = date.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    minutes = minutes < 10 ? '0' + minutes : minutes;
    return `${hours}:${minutes} ${ampm}`;
  }

  function applyWorldEnvironment(envKey) {
    const config = WORLD_CONFIG[envKey] || WORLD_CONFIG.night;

    // Set attributes for CSS variable cascades
    document.documentElement.setAttribute('data-world-env', envKey);
    const stage = document.getElementById('cinematicCampusWorld');
    if (stage) {
      stage.setAttribute('data-world-env', envKey);
    }

    // Update Floating Time & Signature Greeting
    const now = new Date();
    const timeStr = formatTime(now);

    const timeEl = document.getElementById('worldLiveTimeText');
    const symbolEl = document.getElementById('worldPhaseSymbol');
    const greetingEl = document.getElementById('worldSignatureGreeting');

    if (timeEl) {
      timeEl.textContent = `${timeStr} • ${config.name}`;
    }
    if (symbolEl) {
      symbolEl.textContent = config.symbol;
    }
    if (greetingEl) {
      greetingEl.textContent = `"${config.greeting}"`;
    }
  }

  function updateEnvironmentLoop() {
    const now = new Date();
    const activeEnv = currentEnvironment === 'auto' ? getPhaseForHour(now.getHours()) : currentEnvironment;
    applyWorldEnvironment(activeEnv);
  }

  function initWorldTimeEngine() {
    updateEnvironmentLoop();

    // Check every 30 seconds smoothly without page refresh
    if (clockTimer) clearInterval(clockTimer);
    clockTimer = setInterval(updateEnvironmentLoop, 30000);
  }

  /* --------------------------------------------------------------------------
     2. REALISTIC DRIFTING STARFIELD (LIMITED & ELEGANT)
     -------------------------------------------------------------------------- */
  function initWorldStars() {
    const container = document.getElementById('worldStarsField');
    if (!container) return;

    container.innerHTML = '';
    const starCount = 35; // Limited count to avoid particle-demo look

    for (let i = 0; i < starCount; i++) {
      const star = document.createElement('div');
      star.className = 'star-speck';
      const size = Math.random() * 2.2 + 0.8;
      star.style.width = `${size}px`;
      star.style.height = `${size}px`;
      star.style.top = `${Math.random() * 55}%`;
      star.style.left = `${Math.random() * 100}%`;
      star.style.animationDelay = `${(Math.random() * 5).toFixed(1)}s`;
      star.style.animationDuration = `${(Math.random() * 3 + 2.5).toFixed(1)}s`;
      container.appendChild(star);
    }
  }

  /* --------------------------------------------------------------------------
     3. RANDOMIZED WARM WINDOW LIGHT CYCLING
     -------------------------------------------------------------------------- */
  function initWindowGlowCycling() {
    const windows = document.querySelectorAll('.world-window');
    if (!windows.length) return;

    windows.forEach((win, index) => {
      if (index % 2 === 0 || Math.random() > 0.4) {
        win.classList.add('glow-cycle');
        win.style.animationDelay = `${(Math.random() * 6).toFixed(1)}s`;
        win.style.animationDuration = `${(Math.random() * 4 + 5).toFixed(1)}s`;
      }
    });
  }

  /* --------------------------------------------------------------------------
     4. CINEMATIC CAMERA PARALLAX (SMOOTH DEPTH DAMPING)
     -------------------------------------------------------------------------- */
  function initCinematicParallax() {
    if (prefersReducedMotion) return;

    const stage = document.getElementById('cinematicCampusWorld');
    if (!stage) return;

    const layerSky = stage.querySelector('.world-layer-sky');
    const layerCelestial = stage.querySelector('.world-layer-celestial');
    const layerDistant = stage.querySelector('.world-layer-distant-skyline');
    const layerMain = stage.querySelector('.world-layer-main-campus');
    const layerTrees = stage.querySelector('.world-layer-trees');
    const layerRoad = stage.querySelector('.world-layer-road');
    const layerStudents = stage.querySelector('.world-layer-students');
    const layerLamps = stage.querySelector('.world-layer-lamps');
    const floatingTimeline = document.getElementById('floatingTimelineColumn');

    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    let rafId = null;

    function renderParallax() {
      // Smooth lerp damping
      currentX += (targetX - currentX) * 0.05;
      currentY += (targetY - currentY) * 0.05;

      // Specified proportional depth shifts:
      // Sky: 2px | Clouds: 4px | Distant: 7px | Main: 10px | Trees/Road/Lamps: 14px
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
      if (layerRoad) {
        layerRoad.style.transform = `translate3d(${currentX * -14}px, ${currentY * -6}px, 0)`;
      }
      if (layerLamps) {
        layerLamps.style.transform = `translate3d(${currentX * -14}px, ${currentY * -6}px, 0)`;
      }
      if (layerStudents) {
        layerStudents.style.transform = `translate3d(${currentX * -16}px, ${currentY * -7}px, 0)`;
      }

      // Subtle floating depth on timeline if present
      if (floatingTimeline && window.innerWidth >= 1024) {
        floatingTimeline.style.transform = `translate3d(${currentX * 5}px, ${currentY * 5}px, 0)`;
      }

      if (Math.abs(targetX - currentX) > 0.001 || Math.abs(targetY - currentY) > 0.001) {
        rafId = requestAnimationFrame(renderParallax);
      } else {
        rafId = null;
      }
    }

    window.addEventListener('mousemove', (e) => {
      const normX = (e.clientX - window.innerWidth / 2) / (window.innerWidth / 2);
      const normY = (e.clientY - window.innerHeight / 2) / (window.innerHeight / 2);

      targetX = Math.max(-1, Math.min(1, normX));
      targetY = Math.max(-1, Math.min(1, normY));

      if (!rafId) {
        rafId = requestAnimationFrame(renderParallax);
      }
    }, { passive: true });

    window.addEventListener('mouseleave', () => {
      targetX = 0;
      targetY = 0;
      if (!rafId) {
        rafId = requestAnimationFrame(renderParallax);
      }
    }, { passive: true });
  }

  /* --------------------------------------------------------------------------
     5. SIGNATURE CAMPUS PULSE WAVE (EVERY 5 SECONDS)
     -------------------------------------------------------------------------- */
  function initCampusPulseLoop() {
    const pulseDot = document.getElementById('campusPulsePacket');
    if (!pulseDot) return;

    let progress = 0;
    const waypoints = [
      { x: 180, y: 380 }, // Main Gate
      { x: 420, y: 310 }, // Academic Block
      { x: 620, y: 250 }, // Central Library
      { x: 880, y: 290 }, // Student Services
      { x: 1100, y: 360 } // CampusCare Interface
    ];

    function stepPulse() {
      progress += 0.004;
      if (progress > 1) {
        progress = 0;
      }

      const totalSegments = waypoints.length - 1;
      const segIndex = Math.min(Math.floor(progress * totalSegments), totalSegments - 1);
      const segProgress = (progress * totalSegments) - segIndex;

      const p0 = waypoints[segIndex];
      const p1 = waypoints[segIndex + 1];

      const curX = p0.x + (p1.x - p0.x) * segProgress;
      const curY = p0.y + (p1.y - p0.y) * segProgress;

      pulseDot.style.left = `${(curX / 12.4).toFixed(2)}%`;
      pulseDot.style.top = `${(curY / 4.8).toFixed(2)}%`;

      requestAnimationFrame(stepPulse);
    }

    if (!prefersReducedMotion) {
      requestAnimationFrame(stepPulse);
    }
  }

  /* --------------------------------------------------------------------------
     6. DEVELOPER TEST HOOK (CONSOLE TESTING)
     -------------------------------------------------------------------------- */
  window.setCampusEnvironment = function (mode) {
    if (['night', 'sunset', 'afternoon', 'morning', 'sunrise'].includes(mode)) {
      currentEnvironment = mode;
      applyWorldEnvironment(mode);
      console.log(`[CampusCare] Cinematic Environment switched to: ${mode.toUpperCase()}`);
    } else if (mode === 'auto') {
      currentEnvironment = 'auto';
      updateEnvironmentLoop();
      console.log('[CampusCare] Cinematic Environment switched to: AUTO (Local System Time)');
    } else {
      console.warn('[CampusCare] Usage: window.setCampusEnvironment("night" | "sunset" | "afternoon" | "morning" | "sunrise" | "auto")');
    }
  };

})();
