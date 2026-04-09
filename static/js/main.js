/**
 * main.js — Arctic Nord Site JavaScript
 * ======================================
 * Handles:
 *   1. Snowflake canvas animation (hero visual)
 *   2. API demo terminal — live fetch from /api/palette
 *   3. Scroll-aware nav shadow
 *   4. Intersection Observer fade-in for cards
 *
 * No external dependencies — vanilla JS only.
 */

/* ── 1. Snowflake Canvas ─────────────────────────────────────── */

(function snowflakeCanvas() {
  const canvas = document.getElementById("snowCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const W = canvas.width  = canvas.offsetWidth;
  const H = canvas.height = canvas.offsetHeight;

  // Nord colour palette used for flakes
  const COLOURS = ["#D8DEE9", "#88C0D0", "#8FBCBB", "#81A1C1", "#D08770", "#ECEFF4"];

  // Generate a set of snowflake particles
  const FLAKE_COUNT = 80;
  const flakes = Array.from({ length: FLAKE_COUNT }, () => ({
    x: Math.random() * W,
    y: Math.random() * H,
    r: Math.random() * 2.5 + 0.5,        // radius 0.5–3
    speed: Math.random() * 0.6 + 0.2,     // fall speed
    drift: (Math.random() - 0.5) * 0.4,   // horizontal sway
    colour: COLOURS[Math.floor(Math.random() * COLOURS.length)],
    opacity: Math.random() * 0.7 + 0.3,
  }));

  function draw() {
    ctx.clearRect(0, 0, W, H);

    // Faint background gradient so canvas blends with the card
    const grad = ctx.createLinearGradient(0, 0, W, H);
    grad.addColorStop(0, "#3B4252");
    grad.addColorStop(1, "#2E3440");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    // Draw each flake
    flakes.forEach(f => {
      ctx.beginPath();
      ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2);
      ctx.fillStyle = f.colour;
      ctx.globalAlpha = f.opacity;
      ctx.fill();
      ctx.globalAlpha = 1;

      // Move flake
      f.y += f.speed;
      f.x += f.drift;

      // Wrap around when off-screen
      if (f.y > H + 4) { f.y = -4; f.x = Math.random() * W; }
      if (f.x > W + 4) f.x = -4;
      if (f.x < -4)    f.x = W + 4;
    });

    // Draw a simple geometric snowflake in the center
    drawCenterFlake(W / 2, H / 2, 60, Date.now() / 4000);

    requestAnimationFrame(draw);
  }

  /**
   * Draws a six-armed snowflake at (cx, cy) with arm length `size`.
   * Rotates slowly over time using the `t` parameter.
   */
  function drawCenterFlake(cx, cy, size, t) {
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(t);
    ctx.strokeStyle = "#88C0D0";
    ctx.lineWidth = 1.5;
    ctx.globalAlpha = 0.6;

    for (let arm = 0; arm < 6; arm++) {
      ctx.rotate(Math.PI / 3);
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(0, size);

      // Side branches at 1/3 and 2/3 along the arm
      [size * 0.35, size * 0.65].forEach(pos => {
        ctx.moveTo(0, pos);
        ctx.lineTo(size * 0.2,  pos + size * 0.15);
        ctx.moveTo(0, pos);
        ctx.lineTo(-size * 0.2, pos + size * 0.15);
      });
      ctx.stroke();
    }

    ctx.globalAlpha = 1;
    ctx.restore();
  }

  draw();
})();


/* ── 2. API Demo Terminal ────────────────────────────────────── */

(function apiTerminal() {
  const btn    = document.getElementById("loadApiBtn");
  const output = document.getElementById("apiOutput");
  if (!btn || !output) return;

  btn.addEventListener("click", async () => {
    btn.textContent = "Fetching…";
    btn.disabled = true;

    try {
      const res  = await fetch("/api/palette");
      const json = await res.json();

      // Pretty-print a subset so it fits the terminal nicely
      const lines = json.palette.slice(0, 6).map(item =>
        `  { <span class="terminal__key">"name"</span>: <span class="terminal__val">"${item.name}"</span>, ` +
        `<span class="terminal__key">"hex"</span>: <span class="terminal__val">"${item.hex}"</span>, ` +
        `<span class="terminal__key">"group"</span>: <span class="terminal__val">"${item.group}"</span> }`
      );

      output.innerHTML =
        `<span class="terminal__prompt">$ </span>curl /api/palette\n\n` +
        `<span class="terminal__output">{\n` +
        `  "count": ${json.count},\n` +
        `  "palette": [\n` +
        lines.join(",\n") +
        `,\n  <span class="terminal__prompt">  … ${json.count - 6} more</span>\n` +
        `  ]\n}</span>`;

      btn.textContent = "Reload";
      btn.disabled = false;

    } catch {
      output.textContent = "Error: could not reach /api/palette";
      btn.textContent = "Retry";
      btn.disabled = false;
    }
  });
})();


/* ── 3. Scroll-aware nav ─────────────────────────────────────── */

(function navScroll() {
  const nav = document.querySelector(".nav");
  if (!nav) return;
  window.addEventListener("scroll", () => {
    nav.style.boxShadow = window.scrollY > 10
      ? "0 4px 24px rgba(0,0,0,0.45)"
      : "";
  }, { passive: true });
})();


/* ── 4. Fade-in cards on scroll ──────────────────────────────── */

(function cardReveal() {
  const cards = document.querySelectorAll(".card, .swatch, .docs-content h2");
  if (!cards.length || !("IntersectionObserver" in window)) return;

  const style = document.createElement("style");
  style.textContent = `
    .card, .swatch, .docs-content h2 {
      opacity: 0;
      transform: translateY(16px);
      transition: opacity 0.5s ease, transform 0.5s ease;
    }
    .card.visible, .swatch.visible, .docs-content h2.visible {
      opacity: 1;
      transform: translateY(0);
    }
  `;
  document.head.appendChild(style);

  const observer = new IntersectionObserver(
    entries => entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add("visible");
        observer.unobserve(e.target);
      }
    }),
    { threshold: 0.12 }
  );

  cards.forEach(c => observer.observe(c));
})();
