/**
 * CampusCare - 3D Futuristic Interactive Campus Grievance Network
 * High-performance, GPU-accelerated canvas background, 3D card tilt & micro-interactions
 */

(function () {
  'use strict';

  // Check user preference for reduced motion
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  document.addEventListener('DOMContentLoaded', () => {
    init3DNetworkCanvas();
    init3DDashboardTilt();
    initSensorNetworkInteraction();
    initShimmerProgress();
  });

  /* --------------------------------------------------------------------------
     1. 3D INTERACTIVE DIGITAL CAMPUS NETWORK CANVAS
     -------------------------------------------------------------------------- */
  function init3DNetworkCanvas() {
    const canvas = document.getElementById('network3DCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d', { alpha: true });
    let animationFrameId = null;
    let isVisible = true;

    let width = (canvas.width = canvas.parentElement.offsetWidth || window.innerWidth);
    let height = (canvas.height = canvas.parentElement.offsetHeight || 700);

    const isMobile = window.innerWidth < 768;
    // Calibrated node count: responsive, lightweight, battery-efficient
    const baseNodeCount = isMobile ? 24 : Math.min(Math.floor(width / 26), 55);

    // Mouse coordinates & interaction radius
    const mouse = {
      x: -1000,
      y: -1000,
      radius: isMobile ? 80 : 160,
      active: false
    };

    function handleResize() {
      if (!canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.offsetWidth;
      height = canvas.height = canvas.parentElement.offsetHeight;
      initNodes();
    }

    window.addEventListener('resize', handleResize, { passive: true });

    // Track mouse with relative coordinates to canvas
    const heroSection = document.getElementById('heroSection3D') || canvas.parentElement;
    if (heroSection) {
      heroSection.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        mouse.x = e.clientX - rect.left;
        mouse.y = e.clientY - rect.top;
        mouse.active = true;
      }, { passive: true });

      heroSection.addEventListener('mouseleave', () => {
        mouse.active = false;
        mouse.x = -1000;
        mouse.y = -1000;
      }, { passive: true });
    }

    // IntersectionObserver to pause rendering when out of viewport
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        isVisible = entry.isIntersecting;
        if (isVisible && !animationFrameId && !prefersReducedMotion) {
          animate();
        }
      });
    }, { threshold: 0.05 });

    observer.observe(canvas);

    // Theme-dependent colors
    function getThemePalette() {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      return {
        isDark,
        particleColor: isDark ? 'rgba(56, 189, 248, ' : 'rgba(2, 132, 199, ',
        accentColor: isDark ? 'rgba(165, 243, 252, ' : 'rgba(59, 130, 246, ',
        lineColor: isDark ? 'rgba(56, 189, 248, ' : 'rgba(37, 99, 235, ',
        maxDistance: isMobile ? 90 : 130
      };
    }

    let nodes = [];

    class NetworkNode {
      constructor(depthLayer) {
        this.depth = depthLayer; // 0: background (slow/small), 1: mid, 2: foreground
        this.reset(true);
      }

      reset(initial = false) {
        this.x = Math.random() * width;
        this.y = initial ? Math.random() * height : (Math.random() < 0.5 ? -10 : height + 10);
        
        // Depth-based sizing & velocity
        const speedScale = (this.depth + 1) * 0.22;
        this.vx = (Math.random() - 0.5) * speedScale;
        this.vy = (Math.random() - 0.5) * speedScale;
        this.radius = 1.0 + this.depth * 0.85 + (Math.random() * 0.6);
        this.baseAlpha = 0.2 + this.depth * 0.25;
        this.pulsePhase = Math.random() * Math.PI * 2;
        this.isHub = Math.random() > 0.85; // Special glowing hub node
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;
        this.pulsePhase += 0.02;

        // Wrap around boundaries smoothly
        if (this.x < -20) this.x = width + 20;
        if (this.x > width + 20) this.x = -20;
        if (this.y < -20) this.y = height + 20;
        if (this.y > height + 20) this.y = -20;

        // Mouse interaction: subtle repulsion/attraction with spring return
        if (mouse.active) {
          const dx = mouse.x - this.x;
          const dy = mouse.y - this.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < mouse.radius && dist > 0) {
            const force = (1 - dist / mouse.radius) * 1.5;
            const angle = Math.atan2(dy, dx);
            // Slight push away from cursor for interactive ripple feel
            this.x -= Math.cos(angle) * force * (this.depth + 1);
            this.y -= Math.sin(angle) * force * (this.depth + 1);
          }
        }
      }

      draw(palette) {
        const pulse = 0.7 + 0.3 * Math.sin(this.pulsePhase);
        const alpha = Math.min(this.baseAlpha * pulse, 0.95);

        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);

        if (this.isHub) {
          // Glowing hub node with radial flare
          const gradient = ctx.createRadialGradient(
            this.x, this.y, 0,
            this.x, this.y, this.radius * 3.5
          );
          gradient.addColorStop(0, `${palette.accentColor}${alpha})`);
          gradient.addColorStop(0.4, `${palette.particleColor}${alpha * 0.5})`);
          gradient.addColorStop(1, `${palette.particleColor}0)`);

          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.arc(this.x, this.y, this.radius * 3.5, 0, Math.PI * 2);
          ctx.fill();

          ctx.beginPath();
          ctx.arc(this.x, this.y, this.radius * 1.2, 0, Math.PI * 2);
          ctx.fillStyle = `${palette.accentColor}1)`;
          ctx.fill();
        } else {
          ctx.fillStyle = `${palette.particleColor}${alpha})`;
          ctx.fill();
        }
      }
    }

    function initNodes() {
      nodes = [];
      for (let i = 0; i < baseNodeCount; i++) {
        // Distribute across 3 depth planes
        const depth = i % 3;
        nodes.push(new NetworkNode(depth));
      }
    }

    initNodes();

    function drawConnectingLines(palette) {
      const maxDist = palette.maxDistance;
      const maxDistSq = maxDist * maxDist;

      for (let i = 0; i < nodes.length; i++) {
        const n1 = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const n2 = nodes[j];

          // Only connect nodes in compatible depth planes to maintain 3D layering
          if (Math.abs(n1.depth - n2.depth) > 1) continue;

          const dx = n1.x - n2.x;
          const dy = n1.y - n2.y;
          const distSq = dx * dx + dy * dy;

          if (distSq < maxDistSq) {
            const dist = Math.sqrt(distSq);
            const lineAlpha = (1 - dist / maxDist) * 0.22 * ((n1.depth + n2.depth + 1) / 4);

            ctx.beginPath();
            ctx.moveTo(n1.x, n1.y);
            ctx.lineTo(n2.x, n2.y);
            ctx.strokeStyle = `${palette.lineColor}${lineAlpha})`;
            ctx.lineWidth = 0.75 + n1.depth * 0.25;
            ctx.stroke();
          }
        }

        // Draw dynamic line to mouse if active & within range
        if (mouse.active) {
          const mdx = n1.x - mouse.x;
          const mdy = n1.y - mouse.y;
          const mDist = Math.sqrt(mdx * mdx + mdy * mdy);

          if (mDist < mouse.radius * 0.75) {
            const mouseLineAlpha = (1 - mDist / (mouse.radius * 0.75)) * 0.35;
            ctx.beginPath();
            ctx.moveTo(n1.x, n1.y);
            ctx.lineTo(mouse.x, mouse.y);
            ctx.strokeStyle = `${palette.accentColor}${mouseLineAlpha})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }
    }

    function animate() {
      if (!isVisible || prefersReducedMotion) {
        animationFrameId = null;
        return;
      }

      ctx.clearRect(0, 0, width, height);
      const palette = getThemePalette();

      // Update and draw all nodes
      for (let i = 0; i < nodes.length; i++) {
        nodes[i].update();
        nodes[i].draw(palette);
      }

      // Draw interactive connections
      drawConnectingLines(palette);

      animationFrameId = requestAnimationFrame(animate);
    }

    if (!prefersReducedMotion) {
      animate();
    }

    // Re-render immediately on theme change
    window.addEventListener('themeChanged', () => {
      if (!animationFrameId && isVisible && !prefersReducedMotion) {
        animate();
      }
    });
  }

  /* --------------------------------------------------------------------------
     2. SMOOTH 3D TILT EFFECT ON HERO DASHBOARD (LERP INTERPOLATION)
     -------------------------------------------------------------------------- */
  function init3DDashboardTilt() {
    if (prefersReducedMotion || window.innerWidth < 992) return;

    const tiltWrapper = document.getElementById('dashboardTiltContainer');
    const heroSection = document.getElementById('heroSection3D');
    if (!tiltWrapper || !heroSection) return;

    let targetRotateX = 0;
    let targetRotateY = 0;
    let currentRotateX = 0;
    let currentRotateY = 0;
    let isHovering = false;
    let rafId = null;

    const maxTiltAngle = 8; // degrees (subtle, professional)

    function updateTilt() {
      // Linear interpolation (lerp) for liquid smoothness
      currentRotateX += (targetRotateX - currentRotateX) * 0.08;
      currentRotateY += (targetRotateY - currentRotateY) * 0.08;

      tiltWrapper.style.transform = `rotateX(${currentRotateX.toFixed(2)}deg) rotateY(${currentRotateY.toFixed(2)}deg)`;

      if (isHovering || Math.abs(targetRotateX - currentRotateX) > 0.05 || Math.abs(targetRotateY - currentRotateY) > 0.05) {
        rafId = requestAnimationFrame(updateTilt);
      } else {
        tiltWrapper.style.transform = 'rotateX(0deg) rotateY(0deg)';
        rafId = null;
      }
    }

    heroSection.addEventListener('mousemove', (e) => {
      const rect = tiltWrapper.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      const normX = (e.clientX - centerX) / (window.innerWidth / 2);
      const normY = (e.clientY - centerY) / (window.innerHeight / 2);

      // Clamp between -1 and 1
      const clampedX = Math.max(-1, Math.min(1, normX));
      const clampedY = Math.max(-1, Math.min(1, normY));

      targetRotateY = clampedX * maxTiltAngle;
      targetRotateX = -clampedY * maxTiltAngle;
      isHovering = true;

      if (!rafId) {
        rafId = requestAnimationFrame(updateTilt);
      }
    }, { passive: true });

    heroSection.addEventListener('mouseleave', () => {
      targetRotateX = 0;
      targetRotateY = 0;
      isHovering = false;
      if (!rafId) {
        rafId = requestAnimationFrame(updateTilt);
      }
    }, { passive: true });
  }

  /* --------------------------------------------------------------------------
     3. SENSOR NETWORK INTERACTION & LIVE STATUS
     -------------------------------------------------------------------------- */
  function initSensorNetworkInteraction() {
    const nodes = document.querySelectorAll('.sensor-node-item');
    nodes.forEach((node) => {
      node.addEventListener('mouseenter', () => {
        const beacon = node.querySelector('.node-halo-circle');
        if (beacon) {
          beacon.style.transform = 'scale(1.25)';
        }
      });

      node.addEventListener('mouseleave', () => {
        const beacon = node.querySelector('.node-halo-circle');
        if (beacon) {
          beacon.style.transform = '';
        }
      });
    });
  }

  /* --------------------------------------------------------------------------
     4. PROGRESS BAR ANIMATION & LIVE STATUS INITIALIZATION
     -------------------------------------------------------------------------- */
  function initShimmerProgress() {
    const progressFill = document.getElementById('progressFill3D');
    if (!progressFill) return;

    // Trigger smooth fill expansion on viewport view
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          progressFill.style.width = '75%';
          observer.unobserve(progressFill);
        }
      });
    }, { threshold: 0.2 });

    observer.observe(progressFill);
  }

})();
