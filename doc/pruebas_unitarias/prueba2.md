## PRUEBA UNITARIA: INICIO DE SESIÓN 

### 1️⃣ Identificación

* **Nombre de la prueba:** Login correcto
* **Módulo / componente:** *“Iniciar sesión”*

---

### 2️⃣ Objetivo

Verificar que, dados credenciales válidos de un usuario existente, el sistema permite iniciar sesión y accede a la zona privada sin errores.

---

### 3️⃣ Alcance

Se comprueba únicamente la **autenticación** (validación de usuario y contraseña) y la **redirección posterior**. No se prueban recuperación de contraseña, cierre de sesión ni persistencia de sesión prolongada.

---

### 4️⃣ Diseño de la prueba

#### a) Particiones de equivalencia

* **Usuario/Email**

  * Válida: existe en el sistema.
  * Inválida: no existe / formato incorrecto.
* **Contraseña**

  * Válida: coincide con la guardada para el usuario.
  * Inválida: no coincide / vacía.

*(Este caso cubre la partición **válida+válida**.)*

#### b) Precondición relevante

* Existe un usuario registrado previamente:

  * **Usuario:** `Usuario1`
  * **Email:** `Usuario1@example.com`
  * **Contraseña:** `1234`

---

### 5️⃣ Datos de entrada (del formulario de login)

* **Identificador:** `Usuario1` *
* **Contraseña:** `Test1234`

---

### 6️⃣ Pasos de ejecución

1. Navegar a `https://logbait.pythonanywhere.com`.
2. Hacer clic en **“Iniciar sesión”**.
3. En el formulario, introducir el **usuario** y la **contraseña** indicados.
4. Pulsar el botón **“Iniciar sesión”**.
5. Esperar la respuesta del sistema.

---

### 7️⃣ Resultado esperado

* El sistema **no** muestra errores de validación.
* Se **inicia la sesión** del usuario y se **redirige** a la página principal.
* En la interfaz aparecen los créditos del usuario y una pestaña disponible de **datos**.
* La cookie o token de sesión queda establecido.
* Las rutas protegidas quedan accesibles para este usuario.

---

### 8️⃣ Resultado obtenido


* ▢ **Correcto**: redirección a zona privada con sesión activa.
* ▢ **Incorrecto**: mensaje de error / no se establece sesión / redirección incorrecta.

---

### 9️⃣ Criterio de éxito

La prueba **pasa** si, tras enviar credenciales válidas, el sistema inicia sesión y muestra la vista privada correspondiente **sin mensajes de error**.

---

### 🔟 Observaciones / Notas

* Este caso depende de que el usuario exista y la contraseña sea la correcta.
* Para repetir la prueba de forma aislada, asegurarse de no tener una sesión previa activa (por ejemplo, usar ventana privada).
* Casos complementarios:
  * **
  * **Contraseña o usuario incorrectos** → mensaje de error sin iniciar sesión, "Usuario o contraseña incorrectos". 
  * **Campos vacíos** → no permite intentar el inicio de sesión hasta rellenarlos.

