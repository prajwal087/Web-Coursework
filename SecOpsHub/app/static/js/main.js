document.addEventListener('DOMContentLoaded', function() {
  // Sidebar toggle
  var toggleBtn = document.getElementById('sidebarToggle');
  var sidebar = document.querySelector('.sidebar');
  var overlay = document.getElementById('sidebarOverlay');
  if (toggleBtn && sidebar && overlay) {
    function closeSidebar() {
      sidebar.classList.remove('open');
      overlay.classList.remove('open');
    }
    toggleBtn.addEventListener('click', function() {
      sidebar.classList.toggle('open');
      overlay.classList.toggle('open');
    });
    overlay.addEventListener('click', closeSidebar);
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && sidebar.classList.contains('open')) closeSidebar();
    });
  }

  // Toast notifications from flash messages
  var flashMessages = document.querySelectorAll('.flash');
  if (flashMessages.length) {
    var container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    flashMessages.forEach(function(flash) {
      var category = flash.classList.contains('flash-success') ? 'success' :
                     flash.classList.contains('flash-error') ? 'error' : 'warning';
      var icon = category === 'success' ? '\u2713' : category === 'error' ? '\u26A0' : '\u24D8';
      var toast = document.createElement('div');
      toast.className = 'toast toast-' + category;
      toast.innerHTML = '<span class="toast-icon">' + icon + '</span><span class="toast-msg">' + flash.textContent.trim() + '</span><button class="toast-close" aria-label="Dismiss">&times;</button>';
      container.appendChild(toast);
      flash.remove();

      var closeBtn = toast.querySelector('.toast-close');
      closeBtn.addEventListener('click', function() { dismissToast(toast); });
      setTimeout(function() { dismissToast(toast); }, 5000);
    });
  }

  // Keyboard navigation for nav items
  var navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(function(item, index) {
    item.addEventListener('keydown', function(e) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        navItems[(index + 1) % navItems.length].focus();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        navItems[(index - 1 + navItems.length) % navItems.length].focus();
      }
    });
    item.addEventListener('click', function() {
      navItems.forEach(function(n) { n.classList.remove('active'); });
      this.classList.add('active');
      if (window.innerWidth <= 768) {
        var s = document.querySelector('.sidebar');
        var o = document.getElementById('sidebarOverlay');
        if (s) s.classList.remove('open');
        if (o) o.classList.remove('open');
      }
    });
  });

  // Card entrance animations
  var cards = document.querySelectorAll('.card, .tool-card, .soc-stat-panel, .soc-chart-card, .soc-mission-log');
  cards.forEach(function(card, i) {
    if (card.classList.contains('soc-stat-panel') || card.classList.contains('soc-chart-card') || card.classList.contains('soc-mission-log')) return;
    card.style.opacity = '0';
    card.style.transform = 'translateY(10px)';
    card.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
    setTimeout(function() {
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, 60 * i);
  });

  // Form input focus
  document.querySelectorAll('.form-input, .form-select, .form-textarea').forEach(function(input) {
    input.addEventListener('focus', function() {
      var g = this.closest('.form-group');
      if (g) {
        var l = g.querySelector('.form-label');
        if (l) l.style.color = 'var(--cyan)';
      }
    });
    input.addEventListener('blur', function() {
      var g = this.closest('.form-group');
      if (g) {
        var l = g.querySelector('.form-label');
        if (l) l.style.color = '';
      }
    });
    input.addEventListener('input', function() {
      var g = this.closest('.form-group');
      if (g) {
        var errorMsg = g.querySelector('.form-error');
        if (this.validity.valid && errorMsg) {
          errorMsg.remove();
          g.classList.remove('has-error');
        }
      }
    });
  });

  // Status dot animation
  var statusDot = document.querySelector('.status-dot');
  if (statusDot) {
    var colors = ['#22c55e', '#f59e0b', '#22c55e'];
    var ci = 0;
    setInterval(function() {
      statusDot.style.background = colors[ci % colors.length];
      statusDot.style.boxShadow = '0 0 8px ' + colors[ci % colors.length] + '99';
      ci++;
    }, 3000);
  }

  // Button ripple
  document.querySelectorAll('.btn').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      if (e.clientX === 0 && e.clientY === 0) return;
      if (this.classList.contains('btn-primary') || this.classList.contains('btn-danger')) {
        var ripple = document.createElement('span');
        ripple.style.cssText = 'position:absolute;border-radius:50%;background:rgba(255,255,255,.1);transform:scale(0);animation:ripple .4s ease-out;pointer-events:none';
        var rect = this.getBoundingClientRect();
        ripple.style.width = ripple.style.height = Math.max(rect.width, rect.height) + 'px';
        ripple.style.left = (e.clientX - rect.left - rect.height/2) + 'px';
        ripple.style.top = (e.clientY - rect.top - rect.height/2) + 'px';
        this.appendChild(ripple);
        setTimeout(function() { ripple.remove(); }, 400);
      }
    });
  });

  // Form validation
  document.querySelectorAll('form').forEach(function(form) {
    form.addEventListener('submit', function(e) {
      var inputs = this.querySelectorAll('[required]');
      var isValid = true;
      inputs.forEach(function(input) {
        if (!input.value.trim()) {
          isValid = false;
          markInputError(input, 'This field is required');
        } else if (input.type === 'email' && !isValidEmail(input.value)) {
          isValid = false;
          markInputError(input, 'Please enter a valid email address');
        } else if (input.type === 'password' && input.value.length < 12) {
          isValid = false;
          markInputError(input, 'Password must be at least 12 characters');
        }
      });
      if (!isValid) e.preventDefault();
    });
  });

  // Keyboard help
  document.addEventListener('keydown', function(e) {
    if (e.altKey && e.key === 'h') showKeyboardHelp();
  });

  // Ripple keyframe
  var style = document.createElement('style');
  style.textContent = '@keyframes ripple{to{transform:scale(2.5);opacity:0}}';
  document.head.appendChild(style);
});

function dismissToast(toast) {
  toast.style.animation = 'toastOut 0.35s ease-in forwards';
  setTimeout(function() { toast.remove(); }, 350);
}

function markInputError(input, message) {
  var g = input.closest('.form-group');
  if (!g) return;
  g.classList.add('has-error');
  var existingError = g.querySelector('.form-error');
  if (existingError) existingError.remove();
  var errorEl = document.createElement('div');
  errorEl.className = 'form-error';
  errorEl.setAttribute('role', 'alert');
  errorEl.textContent = message;
  g.appendChild(errorEl);
  input.setAttribute('aria-invalid', 'true');
  input.setAttribute('aria-describedby', 'error-' + (Math.random() * 10000 | 0));
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function showKeyboardHelp() {
  console.log('Keyboard shortcuts: Arrow keys to navigate menu, Esc to close sidebar, Tab to navigate form fields');
}
