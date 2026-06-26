// ==================== LOAD SETTINGS FROM API ====================
async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        const data = await res.json();
        if (data.hero_badge) {
            document.getElementById('heroBadgeText').textContent = data.hero_badge;
        }
        if (data.phone) {
            document.querySelectorAll('[data-phone]').forEach(el => {
                el.textContent = data.phone;
                if (el.tagName === 'A') el.href = `tel:${data.phone.replace(/\s/g, '')}`;
            });
        }
        if (data.whatsapp) {
            document.querySelectorAll('[data-whatsapp]').forEach(el => {
                if (el.tagName === 'A') el.href = `https://wa.me/${data.whatsapp}`;
            });
        }
    } catch (e) {
        console.log('Settings loaded from default');
    }
}
loadSettings();

// ==================== LOAD CONTENT FROM API ====================
async function loadContent() {
    try {
        const res = await fetch('/api/content');
        const content = await res.json();
        
        // Hero
        if (content.hero) {
            const heroTitle = document.querySelector('.hero h1');
            const heroDesc = document.querySelector('.hero-desc');
            if (heroTitle && content.hero.title) {
                heroTitle.innerHTML = `${content.hero.title}<br><span class="hero-accent">${content.hero.subtitle || ''}</span>`;
            }
            if (heroDesc && content.hero.description) {
                heroDesc.textContent = content.hero.description;
            }
        }
        
        // About
        if (content.about) {
            const aboutTitle = document.querySelector('.about-content h2');
            const aboutDesc = document.querySelectorAll('.about-content p');
            if (aboutTitle && content.about.title) {
                aboutTitle.innerHTML = content.about.title.replace(/'/g, '&#39;');
            }
            if (aboutDesc[0] && content.about.description) {
                aboutDesc[0].textContent = content.about.description;
            }
            if (aboutDesc[1] && content.about.description2) {
                aboutDesc[1].textContent = content.about.description2;
            }
        }
        
        // Services
        if (content.services) {
            const servicesTitle = document.querySelector('.services .section-header h2');
            const servicesSubtitle = document.querySelector('.services .section-header p');
            if (servicesTitle && content.services.title) {
                servicesTitle.innerHTML = content.services.title;
            }
            if (servicesSubtitle && content.services.subtitle) {
                servicesSubtitle.textContent = content.services.subtitle;
            }
        }
        
        // Service Cards
        const serviceCards = document.querySelectorAll('.service-card');
        for (let i = 1; i <= 8; i++) {
            const key = `service_${i}`;
            if (content[key] && serviceCards[i-1]) {
                const title = serviceCards[i-1].querySelector('h3');
                const desc = serviceCards[i-1].querySelector('p');
                if (title && content[key].title) title.textContent = content[key].title;
                if (desc && content[key].description) desc.textContent = content[key].description;
            }
        }
        
        // Why Us
        if (content.why_us) {
            const whyTitle = document.querySelector('.why-us .section-header h2');
            if (whyTitle && content.why_us.title) {
                whyTitle.innerHTML = content.why_us.title;
            }
        }
        
        // Reason Cards
        const whyCards = document.querySelectorAll('.why-card');
        for (let i = 1; i <= 6; i++) {
            const key = `reason_${i}`;
            if (content[key] && whyCards[i-1]) {
                const title = whyCards[i-1].querySelector('h3');
                const desc = whyCards[i-1].querySelector('p');
                if (title && content[key].title) title.textContent = content[key].title;
                if (desc && content[key].description) desc.textContent = content[key].description;
            }
        }
        
        // Contact
        if (content.contact) {
            const addressEl = document.querySelector('.contact-card p');
            const phoneEls = document.querySelectorAll('[data-phone]');
            if (addressEl && content.contact.address) {
                addressEl.innerHTML = content.contact.address.replace(/, /g, '<br>');
            }
        }
        
        // Working Hours
        if (content.working_hours) {
            const hourRows = document.querySelectorAll('.hour-row');
            if (hourRows[0] && content.working_hours.weekday) {
                hourRows[0].querySelector('span:last-child').textContent = content.working_hours.weekday.split(': ')[1] || '';
            }
            if (hourRows[1] && content.working_hours.saturday) {
                hourRows[1].querySelector('span:last-child').textContent = content.working_hours.saturday.split(': ')[1] || '';
            }
            if (hourRows[2] && content.working_hours.sunday) {
                hourRows[2].querySelector('span:last-child').textContent = content.working_hours.sunday.split(': ')[1] || '';
            }
        }
        
        // Footer
        if (content.footer) {
            const footerDesc = document.querySelector('.footer-brand p');
            const footerCopy = document.querySelector('.footer-bottom p');
            if (footerDesc && content.footer.description) {
                footerDesc.textContent = content.footer.description;
            }
            if (footerCopy && content.footer.copyright) {
                footerCopy.textContent = content.footer.copyright;
            }
        }
        
    } catch (e) {
        console.log('Content loaded from default');
    }
}
loadContent();

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

appointmentForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Get form data
    const formData = new FormData(appointmentForm);
    const data = Object.fromEntries(formData);

    // Save to database
    try {
        const response = await fetch('/api/appointment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.success) {
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
        }
    } catch (error) {
        alert('Bir hata oluştu. Lütfen tekrar deneyin.');
    }
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

// ==================== ACTION CARDS ANIMATION ====================
const actionCards = document.querySelectorAll('.action-card');
actionCards.forEach((card, i) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(30px)';
    setTimeout(() => {
        card.style.transition = 'all 0.6s ease';
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
    }, 800 + (i * 150));
});

console.log('Ölmezler Araç Servis Merkezi - Website loaded successfully!');
