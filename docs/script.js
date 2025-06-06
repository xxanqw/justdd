function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showCopyFeedback(text);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        showCopyFeedback(text);
    });
}

function showCopyFeedback(text) {
    const buttons = document.querySelectorAll('.copy-btn');
    buttons.forEach(btn => {
        if (btn.getAttribute('onclick').includes(text)) {
            const originalHTML = btn.innerHTML;
            
            btn.innerHTML = '<i class="fa-solid fa-clipboard-check"></i>';
            btn.style.background = 'var(--success-color)';
            
            createSimpleFireworks(btn);
            
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.style.background = 'var(--primary-color)';
            }, 2000);
        }
    });
}

function createSimpleFireworks(button) {
    const rect = button.getBoundingClientRect();
    const startX = rect.left + rect.width / 2;
    const startY = rect.top + rect.height / 2;
    
    const colors = ['#FDE68A', '#FDBA74', '#A7F3D0', '#FFFFFF', '#FFD700'];
    
    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        document.body.appendChild(particle);
        
        const size = 4 + Math.random() * 6;
        particle.style.position = 'fixed';
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        particle.style.borderRadius = '50%';
        particle.style.zIndex = '10000';
        particle.style.boxShadow = `0 0 ${6 + Math.random() * 8}px 2px rgba(255,255,255,0.6)`;
        particle.style.pointerEvents = 'none';
        
        particle.style.left = startX + 'px';
        particle.style.top = startY + 'px';
        
        const angle = Math.random() * Math.PI * 2;
        const distance = 40 + Math.random() * 100;
        const endX = startX + Math.cos(angle) * distance;
        const endY = startY + Math.sin(angle) * distance;
        
        const duration = 0.5 + Math.random() * 0.7; 
        particle.animate([
            { transform: 'translate(0, 0) scale(0.8)', opacity: 1 },
            { transform: `translate(${endX - startX}px, ${endY - startY}px) scale(${0.3 + Math.random() * 1.2})`, opacity: 0 }
        ], {
            duration: duration * 1000,
            easing: 'cubic-bezier(0,.9,.57,1)',
            fill: 'forwards'
        });
        
        setTimeout(() => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
            }
        }, duration * 1000);
    }
}

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animated');
        } else {
        }
    });
}, observerOptions);

document.addEventListener('DOMContentLoaded', () => {
    const downloadModal = document.getElementById('downloadModal');
    const heroDownloadBtn = document.getElementById('heroDownloadBtn');
    const downloadCards = document.querySelectorAll('.download-card');
    
    downloadCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = `all 0.3s ease ${0.1 + (index * 0.1)}s`;
    });

    function openModal() {
        if (downloadModal) {
            downloadModal.style.display = 'block';
            document.body.style.overflow = 'hidden'; 
            
            downloadModal.offsetHeight;
            
            setTimeout(() => {
                downloadCards.forEach(card => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                });
            }, 300);
        }
    }

    function closeModal() {
        if (downloadModal) {
            downloadCards.forEach((card, index) => {
                setTimeout(() => {
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                }, index * 50);
            });
            
            const modalContent = downloadModal.querySelector('.modal-content');
            
            setTimeout(() => {
                modalContent.style.transform = 'translateY(20px) scale(0.98)';
                modalContent.style.opacity = '0';
            }, 10);
            
            setTimeout(() => {
                downloadModal.style.display = 'none';
                document.body.style.overflow = 'auto'; 
                
                modalContent.style.transform = '';
                modalContent.style.opacity = '';
                
                downloadCards.forEach((card, index) => {
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                    card.style.transition = `all 0.3s ease ${0.1 + (index * 0.1)}s`;
                });
            }, 500); 
        }
    }

    const closeButton = downloadModal ? downloadModal.querySelector('.close-button') : null;
    
    if (heroDownloadBtn) {
        heroDownloadBtn.addEventListener('click', (e) => {
            e.preventDefault();
            openModal();
        });
    }

    if (closeButton) {
        closeButton.addEventListener('click', closeModal);
    }

    window.addEventListener('click', (event) => {
        if (downloadModal && event.target === downloadModal) {
            closeModal();
        }
    });

    window.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && downloadModal && downloadModal.style.display === 'block') {
            closeModal();
        }
    });

    if (downloadModal) {
        downloadModal.addEventListener('keydown', function(e) {
            if (e.key === 'Tab' && downloadModal.style.display === 'block') {
                const focusableElements = downloadModal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];
                
                if (e.shiftKey && document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
                else if (!e.shiftKey && document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        });
    }

    const animatableElements = document.querySelectorAll('.hero-content, .hero-image');
    animatableElements.forEach(el => {
        el.classList.add('animate-on-scroll');
        observer.observe(el);
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const images = document.querySelectorAll('img[loading="lazy"]');
    
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.addEventListener('load', () => {
                    img.classList.add('loaded');
                });
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
});

function showLoadingSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.innerHTML = `
        <div class="spinner"></div>
        <p>Loading JustDD...</p>
    `;
    
    const style = document.createElement('style');
    style.textContent = `
        .loading-spinner {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: var(--background-color);
            z-index: 9999;
            transition: opacity 0.5s ease;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid var(--border-color);
            border-top: 4px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-spinner p {
            color: var(--text-muted);
            font-size: 1.1rem;
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(spinner);
    
    window.addEventListener('load', () => {
        setTimeout(() => {
            spinner.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(spinner);
                document.head.removeChild(style);
            }, 500);
        }, 1000);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.readyState === 'loading') {
        showLoadingSpinner();
    }
});

function addScrollToTop() {
    const button = document.createElement('button');
    button.innerHTML = '↑';
    button.className = 'scroll-to-top';
    
    const style = document.createElement('style');
    style.textContent = `
        .scroll-to-top {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--primary-color);
            color: var(--background-color);
            border: none;
            cursor: pointer;
            font-size: 1.5rem;
            box-shadow: var(--shadow);
            opacity: 0;
            transform: translateY(100px);
            transition: all 0.3s ease;
            z-index: 1000;
        }
        
        .scroll-to-top.visible {
            opacity: 1;
            transform: translateY(0);
        }
        
        .scroll-to-top:hover {
            background: var(--primary-dark);
            color: var(--background-color);
            transform: translateY(-2px);
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(button);
    
    button.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 500) {
            button.classList.add('visible');
        } else {
            button.classList.remove('visible');
        }
    });
}

addScrollToTop();

function createParticles() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '-1';
    canvas.style.opacity = '0.15';
    
    document.body.appendChild(canvas);
    
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const particles = [];
    const particleCount = 60; 
    
    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 1.5; 
            this.vy = (Math.random() - 0.5) * 1.5;
            this.radius = Math.random() * 2 + 1;
        }
        
        update() {
            this.x += this.vx;
            this.y += this.vy;
            
            if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
            if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
        }
        
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = '#FDE68A'; 
            ctx.fill();
        }
    }
    
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        particles.forEach(particle => {
            particle.update();
            particle.draw();
        });
        
        particles.forEach((particle, i) => {
            particles.slice(i + 1).forEach(otherParticle => {
                const dx = particle.x - otherParticle.x;
                const dy = particle.y - otherParticle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 120) { 
                    ctx.beginPath();
                    ctx.moveTo(particle.x, particle.y);
                    ctx.lineTo(otherParticle.x, otherParticle.y);
                    ctx.strokeStyle = `rgba(253, 230, 138, ${1 - distance / 120})`; 
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            });
        });
        
        requestAnimationFrame(animate);
    }
    
    animate();
    
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

createParticles();

document.addEventListener('DOMContentLoaded', () => {
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(btn => {
        const originalOnClick = btn.onclick;
        btn.onclick = function(e) {
            if (originalOnClick) originalOnClick.call(this, e);
        };
    });
});

