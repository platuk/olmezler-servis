// ==================== NAVBAR ====================
const navbar = document.getElementById('navbar');
const mobileToggle = document.getElementById('mobileToggle');
const navLinks = document.getElementById('navLinks');

// Scroll effect
window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 50);
});

// Mobile menu
mobileToggle.addEventListener('click', () => {
    navLinks.classList.toggle('active');
    mobileToggle.classList.toggle('active');
});

// Close mobile menu on link click
navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
        navLinks.classList.remove('active');
        mobileToggle.classList.remove('active');
    });
});

// Close menu on outside click
document.addEventListener('click', (e) => {
    if (!navLinks.contains(e.target) && !mobileToggle.contains(e.target)) {
        navLinks.classList.remove('active');
        mobileToggle.classList.remove('active');
    }
});

// ==================== SCROLL ANIMATIONS ====================
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const delay = entry.target.dataset.delay || 0;
            setTimeout(() => {
                entry.target.classList.add('aos-animate');
            }, delay);
        }
    });
}, observerOptions);

document.querySelectorAll('[data-aos]').forEach(el => observer.observe(el));

// ==================== APPOINTMENT FORM ====================
const appointmentForm = document.getElementById('appointmentForm');
const successModal = document.getElementById('successModal');

// Set min date to today
const dateInput = document.getElementById('date');
const today = new Date().toISOString().split('T')[0];
dateInput.setAttribute('min', today);

appointmentForm.addEventListener('submit', (e) => {
    e.preventDefault();

    // Get form data
    const formData = new FormData(appointmentForm);
    const data = Object.fromEntries(formData);

    // Build WhatsApp message
    let message = `🔧 *RANDEVU TALEBİ*\n\n`;
    message += `👤 *Ad Soyad:* ${data.name}\n`;
    message += `📞 *Telefon:* ${data.phone}\n`;
    
    if (data.vehicle) message += `🚗 *Araç:* ${data.vehicle}\n`;
    message += `🔧 *Hizmet:* ${data.service}\n`;
    if (data.date) message += `📅 *Tarih:* ${formatDate(data.date)}\n`;
    if (data.time) message += `⏰ *Saat:* ${data.time}\n`;
    if (data.message) message += `💬 *Açıklama:* ${data.message}\n`;

    message += `\n_Ölmezler Araç Servis Merkezi web sitesinden gönderildi._`;

    // Open WhatsApp with pre-filled message
    const whatsappURL = `https://wa.me/905379292946?text=${encodeURIComponent(message)}`;
    window.open(whatsappURL, '_blank');

    // Show success modal
    showModal();

    // Reset form
    appointmentForm.reset();
});

function formatDate(dateStr) {
    const parts = dateStr.split('-');
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

// ==================== MODAL ====================
function showModal() {
    successModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    successModal.classList.remove('active');
    document.body.style.overflow = '';
}

// Close modal on overlay click
successModal.addEventListener('click', (e) => {
    if (e.target === successModal) closeModal();
});

// Close modal on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});

// ==================== PHONE FORMAT ====================
const phoneInput = document.getElementById('phone');
phoneInput.addEventListener('input', (e) => {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length > 11) value = value.slice(0, 11);
    
    if (value.length >= 7) {
        value = value.replace(/(\d{4})(\d{3})(\d{2})(\d{2})/, '$1 $2 $3 $4');
    } else if (value.length >= 4) {
        value = value.replace(/(\d{4})(\d+)/, '$1 $2');
    }
    
    e.target.value = value;
});

// ==================== SMOOTH SCROLL ====================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ==================== ACTIVE NAV LINK ====================
const sections = document.querySelectorAll('section[id]');

window.addEventListener('scroll', () => {
    const scrollY = window.scrollY + 100;
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.offsetHeight;
        const sectionId = section.getAttribute('id');
        
        const navLink = document.querySelector(`.nav-links a[href="#${sectionId}"]`);
        if (navLink) {
            if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
                navLink.style.color = 'var(--accent)';
            } else {
                navLink.style.color = '';
            }
        }
    });
});

// ==================== MOBILE TOGGLE ANIMATION ====================
const style = document.createElement('style');
style.textContent = `
    .mobile-toggle.active span:nth-child(1) {
        transform: rotate(45deg) translate(5px, 5px);
    }
    .mobile-toggle.active span:nth-child(2) {
        opacity: 0;
    }
    .mobile-toggle.active span:nth-child(3) {
        transform: rotate(-45deg) translate(5px, -5px);
    }
`;
document.head.appendChild(style);

// ==================== COUNTER ANIMATION ====================
function animateCounters() {
    const counters = document.querySelectorAll('.stat-num');
    
    counters.forEach(counter => {
        const target = counter.textContent;
        const num = parseInt(target);
        const suffix = target.replace(/[0-9]/g, '');
        
        if (isNaN(num)) return;
        
        let current = 0;
        const increment = num / 50;
        const timer = setInterval(() => {
            current += increment;
            if (current >= num) {
                counter.textContent = target;
                clearInterval(timer);
            } else {
                counter.textContent = Math.floor(current) + suffix;
            }
        }, 30);
    });
}

// Trigger counter animation when hero is visible
const heroObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateCounters();
            heroObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

const heroStats = document.querySelector('.hero-stats');
if (heroStats) heroObserver.observe(heroStats);

console.log('Ölmezler Araç Servis Merkezi - Website loaded successfully!');
