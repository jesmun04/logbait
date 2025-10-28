# PRUEBAS UNITARIAS: BLACKJACK

## PRUEBA 1: Inicio de partida con apuesta válida

### Identificación
- **Nombre**: Inicio de partida con apuesta válida
- **Módulo**: Juego "Blackjack"

### Objetivo
Comprobar que el sistema permite iniciar una partida correctamente cuando el usuario introduce una cantidad válida y que la interfaz se actualiza para mostrar la mesa de juego.

### Alcance
Se evalúa solo la funcionalidad de inicio de partida (no se contemplan acciones de juego posteriores como pedir, plantar o doblar).

### Diseño de la prueba
**Particiones de equivalencia:**
- Parámetro: cantidad de apuesta
  - Clases válidas: valores numéricos positivos ≤ saldo
  - Clases inválidas: 0, negativos, texto, null, undefined, valor > saldo

**Valores límite:**
- Límite inferior: 1
- Límite superior: igual al saldo disponible
  
### Datos de entrada
Apuesta = 50
Saldo = 1000

### Pasos de ejecución
1. Acceder al módulo “Blackjack”.
2. Establecer saldo del usuario en 1000 €.
3. Ingresar la cantidad de apuesta: 50.
4. Ejecutar botón 'Iniciar simulación'
5. Observar el comportamiento de la interfaz:
-Oculta el panel de apuesta.
-Muestra la mesa de juego.
-Muestra las dos cartas iniciales del jugador y una visible del crupier.

### Resultado esperado
- `Saldo = 950´
- El panel de apuesta desaparece.
- Se muestra la mesa de juego con cartas iniciales.

---

## PRUEBA 2: VALIDACIÓN DE APUESTA CON SALDO INSUFICIENTE

### Identificación
- **Nombre**: Validación de apuesta con saldo insuficiente
- **Módulo**: Juego "Blackjack"

### Objetivo
Comprobar que el sistema impide iniciar una partida cuando el jugador intenta apostar una cantidad mayor a su saldo disponible, mostrando el mensaje de error correspondiente y sin alterar el estado del juego.

### Alcance
Se evalúa únicamente la validación previa al inicio del juego, sin ejecutar la simulación ni modificar estadísticas.

### Diseño de la prueba
**Particiones de equivalencia:**
- Parámetro: Cantidad de apuesta
  - Clases válidas: valores ≤ saldo
  - Clases inválidas: valores > saldo

### Datos de entrada
Saldo = 1000
Apuesta = 1500

### Pasos de ejecución
1. Acceder al módulo “Blackjack”.
2. Establecer el saldo del usuario en 1000 €.
3. Introducir en el campo de apuesta el valor 1500.
4. Ejecutar el botón 'iniciar simulación'.

### Resultado esperado
- Aparece una alerta con el mensaje “FONDOS INSUFICIENTES”.
- El saldo no cambia.

---

## PRUEBA 3: BOTONES DE APUESTA RÁPIDA RELLENAN EL INPUT CORRECTAMENTE

### Identificación
- **Nombre**: BOTONES DE APUESTA RÁPIDA RELLENAN EL INPUT CORRECTAMENTE
- **Módulo**: Juego "Blackjack"

### Objetivo
Verificar que los botones de apuesta rápida (25, 50, 100) rellenan el campo de entrada de apuesta con el valor correspondiente y que el valor resultante es válido para iniciar una partida.

### Alcance
Se evalúa únicamente la funcionalidad de los botones de apuesta rápida y la actualización del campo de entrada, sin iniciar la partida ni efectuar cambios en el saldo.

### Diseño de la prueba
**Particiones de equivalencia:**
- Parámetro: Botón de apuesta rápida pulsado
  - Clases válidas: botones existentes
  - Clases inválidas: botones inexistentes

### Datos de entrada
Ninguno en el sentido de parámetros de función; la prueba simula clicks en los botones:
 -Botones objetivo: button con onclick="apuestaRapida(25)", apuestaRapida(50), apuestaRapida(100)
 -Campo de entrada: elemento con id cantidad

### Pasos de ejecución
1. Acceder al módulo “Blackjack”.
2. Asegurarse de que el campo 'Apuesta' existe y tiene un valor inicial
3. Ejecutar la acción asociada al botón de 25
4. Comprobar el valor del input
5. Repetir para los botones 50 y 100

### Resultado esperado
- Tras pular el boton de 25,'Apuesta' = "25".
- Tras pular el boton de 50,'Apuesta' = "50".
- Tras pular el boton de 100,'Apuesta' = "100".

---

## PRUEBA 4: EJECUCIÓN COMPLETA DE CARRERA EXITOSA

### Identificación
- **Nombre**: Carrera completa con apuesta ganadora
- **Módulo**: Juego "Carrera de Caballos" completo

### Objetivo
Verificar el flujo completo desde la apuesta hasta el resultado ganador.

### Datos de entrada

saldoInicial = 100
cantidadApuesta = 50
caballoSeleccionado = 1 // Relámpago
caballoGanador = 1 // Relámpago gana


### Pasos de ejecución
1. Iniciar sesión con usuario válido
2. Acceder a "Carrera de Caballos"
3. Seleccionar Relámpago
4. Apostar 50 créditos
5. Ejecutar carrera
6. Simular victoria de Relámpago
7. Verificar resultados

### Resultado esperado
- Se descuenta apuesta del saldo: 100 - 50 = 50
- Se calcula ganancia: 50 × 1.5 = 75
- Nuevo saldo: 50 + 75 = 125
- Se muestra mensaje: "¡GANASTE! 🎉"
- Se actualiza balance en interfaz

---

## PRUEBA 5: RESETEO DE CARRERA

### Identificación
- **Nombre**: Reseteo correcto del estado del juego
- **Módulo**: Funcionalidad de reinicio

### Objetivo
Comprobar que la función `reiniciarCarrera()` restablece correctamente el estado del juego.

### Pasos de ejecución
1. Configurar estado con caballo seleccionado y carrera en curso
2. Ejecutar `reiniciarCarrera()`
3. Verificar estado resultante

### Resultado esperado
- `caballoSeleccionado = null`
- `carreraEnCurso = false`
- Todos los caballos en posición inicial (left: 0px)
- Botones de selección en estado "outline"
- Información de apuesta limpiada
- Botón "Iniciar Carrera" habilitado

---

## PRUEBA 6: COMUNICACIÓN CON BACKEND

### Identificación
- **Nombre**: Envío correcto de resultados al servidor
- **Módulo**: API Integration

### Objetivo
Verificar que los datos se envían correctamente al endpoint del servidor.

### Datos de entrada
resultado = "ganada"
cantidad = 50
ganancia = 75
caballoApostado = 1
caballoGanador = 1

### Pasos de ejecución
1. Ejecutar `enviarResultadoCaballos()` con datos de prueba
2. Verificar estructura de la petición HTTP
3. Comprobar manejo de respuesta exitosa

### Resultado esperado
- Petición POST a '/api/caballos/apostar'
- Headers incluyen 'Content-Type' y CSRF Token
- Body contiene todos los datos necesarios
- En respuesta exitosa, actualiza balance en interfaz

---

## PRUEBA 7: VALIDACIÓN DE ENTRADA DE MONTO

### Identificación
- **Nombre**: Validación de entrada de cantidad
- **Módulo**: Control de formularios

### Objetivo
Comprobar que el input de cantidad valida correctamente los valores.

### Casos de prueba:
1. **Cantidad mayor al saldo**: Debe ajustarse al saldo máximo
2. **Cantidad negativa**: No permitida (min="1")
3. **Valor decimal**: Permitido (step="1" pero parseFloat lo maneja)
4. **Campo vacío**: Alert "Ingresa una cantidad válida"

---

## PRUEBA 8: ANIMACIÓN Y ESTADOS VISUALES

### Identificación
- **Nombre**: Estados visuales durante la carrera
- **Módulo**: Interfaz de usuario

### Objetivo
Verificar los cambios visuales durante la ejecución de la carrera.

### Verificaciones:
- Botón "Iniciar Carrera" se deshabilita durante carrera
- Caballos se mueven progresivamente hacia la meta
- Caballo ganador tiene animación "pulse"
- Posiciones se reinician correctamente

---
