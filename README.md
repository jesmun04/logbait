<h1 style="text-align: center;">🎰 LogBait, Plataforma de Apuestas Online</h1>

<img width="512" height="512" alt="image" src="https://github.com/user-attachments/assets/bd5739a7-5476-4d39-aa36-6538b0d02da6" />

## [LogBait.com](https://logbait.pythonanywhere.com/)

**LogBait** es una plataforma web de apuestas desarrollada como proyecto académico.  
Su objetivo es ofrecer una experiencia sencilla, segura y responsable para los usuarios interesados en realizar apuestas en línea de manera simulada.

> [!NOTE]
> Este proyecto no gestiona dinero real. Todas las operaciones y apuestas son ficticias y tienen únicamente fines educativos.

---

## 🧩 Descripción general

LogBait permite a los usuarios registrarse, gestionar su saldo virtual, realizar apuestas en distintos juegos y consultar los resultados obtenidos.  
El proyecto se ha desarrollado aplicando **metodologías ágiles**, con iteraciones cortas y una planificación basada en **historias de usuario**.

Actualmente se encuentra en su primera fase **MVP (Producto Mínimo Viable)**, cuyo propósito es ofrecer una versión funcional que cubra las características esenciales de una casa de apuestas online.
Según vayamos avanzando en el proyecto, seguiremos implementando historias de usuario que aportarán versatilidad y comodidad al usuario. las funcionalidades concretas de estas historias se pueden observar en el apartado de **Próximos pasos**.

---

## 🎯 Objetivo del MVP

El MVP busca validar la **viabilidad y usabilidad básica** de la plataforma.  
Incluye las funcionalidades mínimas necesarias para que un usuario pueda:

1. Registrarse e iniciar sesión.  
2. Gestionar su perfil y saldo virtual.  
3. Establecer límites de depósito para fomentar el juego responsable.  
4. Realizar apuestas simples y visualizar sus resultados.
5. Consultar su saldo y su historial básico de movimientos.

---

## ⚙️ Funcionalidades del MVP

### 👤 Gestión de usuarios
- Registro e inicio de sesión seguros.
- Perfil editable con información básica del usuario.
- Cierre de sesión.  

### 💰 Gestión de saldo
- Depósito y retirada de saldo virtual.  
- Límite de depósito configurable por el usuario.  
- Aviso cuando se alcance o se aproxime el límite establecido.  
- Visualización clara del saldo disponible.

### 🎲 Apuestas
- Interfaz sencilla para realizar apuestas en una modalidad de juego (póker o blackjack).  
- Actualización automática de resultados (ganancia o pérdida).  
- Ajuste del saldo según el resultado.  

### 📊 Resultados e historial
- Visualización de resultados recientes.  
- Historial básico de depósitos y pérdidas.

### 🎰 Ruleta Multijugador
- **Juego en tiempo real** con otros jugadores usando WebSockets (Socket.IO).
- **Apuestas secretas**: cada jugador coloca sus apuestas de forma privada (no se revelan a otros jugadores).
- **Sincronización automática**: la ruleta gira cuando todos los jugadores han confirmado sus apuestas o después de 30 segundos.
- **Interfaz idéntica al juego individual**: cada jugador dispone de su propio tablero con chips arrastrables.
- **Múltiples tipos de apuestas**: pleno, caballo, calle, cuadro, línea, docena, columna, rojo/negro, par/impar, 1-18, 19-36.
- **Chat en tiempo real**: comunicación entre jugadores durante la partida.
- **Estadísticas en vivo**: visualización del saldo y estado de los jugadores.

Para más información, consulta:
- 📋 [RULETA_MULTIJUGADOR_RESUMEN.md](./RULETA_MULTIJUGADOR_RESUMEN.md) — Resumen arquitectónico
- 📘 [QUICK_START_RULETA.md](./QUICK_START_RULETA.md) — Guía rápida para desarrolladores
- 📗 [IMPLEMENTACION_RULETA_MULTIJUGADOR.md](./IMPLEMENTACION_RULETA_MULTIJUGADOR.md) — Documentación técnica

---


## 📆 Metodología de desarrollo

El proyecto se ha desarrollado aplicando **métodos ágiles**, priorizando la entrega temprana de valor y la iteración constante.  
Las historias de usuario se gestionan en distribuidas en sprints con prioridades **Muy Alta, Alta, Media y Opcional**.

---

## 💡 Próximos pasos

Las futuras iteraciones del proyecto incluirán:
- Más modalidades de juegos multijugador (Póker, Blackjack, Carrera de Caballos multijugador).  
- Sistema de recompensas y promociones con logros.  
- Mejora del sistema de chat (emojis, reacciones, mutes).  
- Estadísticas avanzadas de rendimiento y actividad con gráficos.  
- Soporte para múltiples servidores con sincronización Redis (escalabilidad).  
- Mejoras de accesibilidad y experiencia de usuario en dispositivos móviles.  
- Sistema de torneos y ligas entre jugadores.

---

## ⚠️ Aviso legal

Este proyecto tiene **fines exclusivamente académicos**.  
No se maneja dinero real ni se promueve el juego con apuestas monetarias.  
El contenido está destinado a la **evaluación de conocimientos técnicos y metodológicos**.

---
