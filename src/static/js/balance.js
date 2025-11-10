// blackjack-multijugador.js
// -------------------------------------------------------------
// Requisitos en la plantilla:
//  - <script>window.salaId = {{ sala.id }};</script>
//  - El header tiene: $<span id="balance">{{ "%.2f"|format(current_user.balance) }}</span>
//  - Existen funciones render(st) y startCountdown(st)
// -------------------------------------------------------------

(function () {
  // Usa el socket global si ya existe; si no, crea uno nuevo.
  const socket = window.socket || io();
  window.socket = socket;

  // Id de sala expuesto desde la plantilla
  const salaId = window.salaId;

  // Id del usuario actual (string) — importante para mapear con st.jugadores
  const meId = "{{ current_user.get_id() }}";

  // --- Helper: actualizar el saldo del header (solo número; el $ está fuera del <span>) ---
  function setHeaderBalance(v) {
    const el = document.getElementById('balance');
    if (!el) return;
    el.textContent = Number(v).toFixed(2);
    el.dataset.balance = v;
  }

  // === Conexión y entrada a sala ===
  socket.on('connect', () => {
    socket.emit('join_sala_blackjack', { sala_id: salaId });
  });

  socket.on('error_blackjack', (e) => {
    alert((e && e.msg) || 'Error');
  });

  // === Estado de la partida ===
  socket.on('estado_blackjack', (st) => {
    // Guarda último estado (si lo usas en otros sitios)
    window.lastState = st;

    // Pinta mesa y temporizador (propias de tu proyecto)
    render(st);
    startCountdown(st);

    // Sincroniza el saldo del header con el del usuario actual
    if (st && st.jugadores && st.jugadores[meId]) {
      setHeaderBalance(st.jugadores[meId].balance);
    }
  });

  // === Actualización inmediata del saldo tras APOSTAR (server -> cliente) ===
  socket.on('balance_update', (data) => {
    if (data && typeof data.balance !== 'undefined') {
      setHeaderBalance(data.balance);
    }
  });

  // -------------------------------------------------------------
  // Exponer helpers para que los botones puedan llamar a emitir eventos
  // (En tu HTML puedes hacer onclick="apostarBJ(importeInput.value)" etc.)
  // -------------------------------------------------------------
  window.apostarBJ = function (cantidad) {
    const n = Number(cantidad);
    if (!salaId || !Number.isFinite(n) || n <= 0) return;
    socket.emit('apostar_blackjack', { sala_id: salaId, cantidad: n });
  };

  window.iniciarBJ = function () {
    if (!salaId) return;
    socket.emit('iniciar_ronda_blackjack', { sala_id: salaId });
  };

  window.hitBJ = function () {
    if (!salaId) return;
    socket.emit('hit_blackjack', { sala_id: salaId });
  };

  window.standBJ = function () {
    if (!salaId) return;
    socket.emit('stand_blackjack', { sala_id: salaId });
  };

  window.revanchaBJ = function () {
    if (!salaId) return;
    socket.emit('voto_revancha', { sala_id: salaId });
  };
})();


