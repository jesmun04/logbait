class MotivationalSystem {
    constructor() {
        this.lossStreak = 0;
        this.init();
    }

    init() {
        // Crear el modal si no existe
        if (!document.getElementById('motivational-modal')) {
            this.createModal();
        }
        this.bindEvents();
    }

    createModal() {
        const modalHTML = `
            <div id="motivational-modal" class="motivational-modal" style="display: none;">
                <div class="motivational-content">
                    <div class="motivational-icon">💪</div>
                    <h3 class="motivational-title" id="motivational-title"></h3>
                    <p class="motivational-message" id="motivational-message"></p>
                    <button class="btn btn-primary motivational-btn" id="motivational-close-btn">
                        ¡Vamos de nuevo!
                    </button>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    bindEvents() {
        // Cerrar modal con el botón
        document.addEventListener('click', (e) => {
            if (e.target.id === 'motivational-close-btn') {
                this.closeModal();
            }
        });

        // Cerrar modal al hacer click fuera
        document.addEventListener('click', (e) => {
            if (e.target.id === 'motivational-modal') {
                this.closeModal();
            }
        });

        // Cerrar con tecla ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isModalOpen()) {
                this.closeModal();
            }
        });
    }

    checkMotivationalMessage(resultado) {
        if (resultado === 'perdida' || resultado === 'derrota') {
            this.lossStreak++;
            
            // Mostrar mensaje después de 3, 5, y cada 5 pérdidas consecutivas
            if (this.lossStreak === 3 || this.lossStreak === 5 || this.lossStreak % 5 === 0) {
                this.showMotivationalMessage();
            }
        } else {
            // Resetear la racha de pérdidas al ganar
            this.lossStreak = 0;
        }
    }

    showMotivationalMessage() {
        const randomIndex = Math.floor(Math.random() * motivationalMessages.length);
        const selectedMessage = motivationalMessages[randomIndex];
        
        const modal = document.getElementById('motivational-modal');
        const titleElement = document.getElementById('motivational-title');
        const messageElement = document.getElementById('motivational-message');
        const iconElement = document.querySelector('.motivational-icon');
        
        titleElement.textContent = selectedMessage.title;
        messageElement.textContent = selectedMessage.message;
        iconElement.textContent = selectedMessage.icon;
        
        modal.style.display = 'flex';
        
        // Auto-cerrar después de 8 segundos
        this.autoCloseTimer = setTimeout(() => {
            if (this.isModalOpen()) {
                this.closeModal();
            }
        }, 8000);
    }

    closeModal() {
        const modal = document.getElementById('motivational-modal');
        modal.style.display = 'none';
        
        if (this.autoCloseTimer) {
            clearTimeout(this.autoCloseTimer);
        }
    }

    isModalOpen() {
        const modal = document.getElementById('motivational-modal');
        return modal && modal.style.display !== 'none';
    }

    // Método para reiniciar la racha manualmente
    resetStreak() {
        this.lossStreak = 0;
    }

    // Método para obtener la racha actual
    getCurrentStreak() {
        return this.lossStreak;
    }
}

// Inicializar el sistema global
window.motivationalSystem = new MotivationalSystem();

// Función global para compatibilidad con código existente
window.checkMotivationalMessage = function(resultado) {
    window.motivationalSystem.checkMotivationalMessage(resultado);
};

// Función global para cerrar el modal
window.closeMotivationalModal = function() {
    window.motivationalSystem.closeModal();
};