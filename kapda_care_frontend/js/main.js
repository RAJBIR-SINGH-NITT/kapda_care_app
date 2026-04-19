// ============================================================
// KAPDA CARE — Main JS (Landing Page)
// ============================================================

// Navbar scroll effect
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 20) navbar.classList.add('scrolled');
  else navbar.classList.remove('scrolled');
});

// Hamburger menu
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');
if (hamburger && mobileMenu) {
  hamburger.addEventListener('click', () => {
    mobileMenu.classList.toggle('open');
  });
}

// Scroll reveal
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.style.opacity = '1';
      e.target.style.transform = 'translateY(0)';
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.service-card, .step-card, .stat-card, .discount-card').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(20px)';
  el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  observer.observe(el);
});

// If user is logged in, update nav
document.addEventListener('DOMContentLoaded', () => {
  const token = localStorage.getItem('kc_token');
  const user  = JSON.parse(localStorage.getItem('kc_user') || 'null');
  if (token && user) {
    const navLinks = document.querySelector('.nav-links');
    if (navLinks) {
      const lastTwo = navLinks.querySelectorAll('li:nth-last-child(-n+2)');
      lastTwo.forEach(li => li.style.display = 'none');
      const dashLink = document.createElement('li');
      const role = user.role;
      const href = (role === 'admin' || role === 'vendor') ? '/pages/vendor-dashboard.html' : '/pages/dashboard.html';
      dashLink.innerHTML = `<a href="${href}" class="btn-primary">My Dashboard →</a>`;
      navLinks.appendChild(dashLink);
    }
  }
});

