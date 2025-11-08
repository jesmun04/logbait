// Actualización automática de salas
// (funciona solamente si el elemento dentro del cual se incluye la plantilla de lista de salas tiene id="salas-container")
document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    const container = document.querySelector('#salas-container');

    // Helper: obtener el número de página actual desde la URL
    function getCurrentPage() {
        const params = new URLSearchParams(window.location.search);
        return parseInt(params.get('page')) || 1;
    }

    // Cargar las salas actuales (HTML parcial)
    function actualizarSalas(page = getCurrentPage()) {
        const url = `?page=${page}`;
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(response => {
                if (!response.ok) throw new Error('Error en la respuesta del servidor');
                return response.text();
            })
            .then(html => {
                // Reemplaza solo el contenido del contenedor
                container.innerHTML = html;

                // Reasignar listeners a los nuevos botones de paginación
                inicializarPaginacion();
            })
            .catch(error => console.error('Error actualizando salas:', error));
    }

    // Interceptar clicks en la paginación (para evitar recargar la página completa)
    function inicializarPaginacion() {
        const pagLinks = container.querySelectorAll('.pagination a.page-link');
        pagLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const pageMatch = this.href.match(/page=(\d+)/);
                const page = pageMatch ? parseInt(pageMatch[1]) : 1;
                actualizarSalas(page);
                // Actualizar URL sin recargar
                window.history.replaceState({}, '', `?page=${page}`);
            });
        });
    }

    // Inicializar los eventos de Socket.IO
    socket.on('user_joined', (data) => {
        console.log('Usuario se unió:', data);
        actualizarSalas();
    });

    socket.on('user_left', (data) => {
        console.log('Usuario salió:', data);
        actualizarSalas();
    });

    // Actualizar periódicamente
    setInterval(() => actualizarSalas(), 5000);

    // Inicialización inicial
    inicializarPaginacion();
});