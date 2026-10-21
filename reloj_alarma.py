"""
Proyecto: Desarrollo de un Reloj con Python
Materia: Estructuras de Datos

Reloj analógico con interfaz gráfica y alarma como funcionalidad
adicional.

Código puro: la ÚNICA importación es tkinter, el módulo que trae
Python para crear ventanas (sin él la única forma de tener interfaz
sería HTML/CSS, que está prohibido). Todo lo demás es código propio:
    - seno() y coseno()  -> calculados con series de Taylor
    - Hora.actual()      -> lee el reloj del sistema a través de la
                            ventana de tkinter (comando "clock")

Organización (cada parte con una sola responsabilidad):
    Hora            -> guarda una hora y la lee del sistema
    LogicaReloj     -> calcula los ángulos de las manecillas
    Alarma          -> guarda, valida, activa/desactiva la alarma
    RelojAnalogico  -> dibuja el reloj en un Canvas
    Aplicacion      -> arma la ventana y conecta todo
"""

import tkinter as tk


# ----------------------------------------------------------------------
# 0. MATEMÁTICAS PROPIAS (sin la librería math)
# ----------------------------------------------------------------------
PI = 3.141592653589793


def seno(grados):
    """Seno de un ángulo en grados, con la serie de Taylor:

        sen(x) = x - x^3/3! + x^5/5! - x^7/7! + ...

    Primero se lleva el ángulo al rango -180..180 para que la serie
    converja rápido; con 15 términos el error es menor a 0.0000001.
    """
    grados = (grados + 180) % 360 - 180
    x = grados * PI / 180          # grados -> radianes
    termino = x                    # primer término de la serie
    suma = x
    for n in range(1, 15):
        # cada término sale del anterior: * (-x^2) / ((2n)(2n+1))
        termino = -termino * x * x / ((2 * n) * (2 * n + 1))
        suma += termino
    return suma


def coseno(grados):
    """cos(a) = sen(a + 90°)"""
    return seno(grados + 90)


# ----------------------------------------------------------------------
# 1. HORA (lee la hora del sistema sin datetime)
# ----------------------------------------------------------------------
class Hora:
    """Una hora del día: hora (0-23), minuto, segundo y milisegundo."""

    def __init__(self, hora, minuto, segundo, milisegundo=0):
        self.hora = hora
        self.minuto = minuto
        self.segundo = segundo
        self.milisegundo = milisegundo

    @staticmethod
    def actual(ventana):
        """Lee la hora del computador.

        Tkinter trae por dentro el lenguaje Tcl, que tiene el comando
        "clock". Con ventana.tk.call(...) le pedimos al sistema:
          - los milisegundos transcurridos desde 1970
          - y esa fecha formateada como "HH MM SS" en hora local.
        """
        total_ms = int(ventana.tk.call("clock", "milliseconds"))
        total_s = total_ms // 1000
        texto = str(ventana.tk.call("clock", "format", total_s,
                                    "-format", "%H %M %S",
                                    "-timezone", ":localtime"))
        hora, minuto, segundo = (int(parte) for parte in texto.split())
        return Hora(hora, minuto, segundo, total_ms % 1000)

    def texto(self):
        return f"{self.hora:02d}:{self.minuto:02d}:{self.segundo:02d}"


# ----------------------------------------------------------------------
# 2. LÓGICA DEL RELOJ (no sabe nada de la interfaz)
# ----------------------------------------------------------------------
class LogicaReloj:
    """Convierte una hora en los ángulos de las tres manecillas.

    Los ángulos se miden en grados desde las 12, en sentido horario.
    """

    @staticmethod
    def angulos(ahora):
        """Devuelve (angulo_hora, angulo_minuto, angulo_segundo)."""
        segundos = ahora.segundo
        minutos = ahora.minuto
        horas = ahora.hora % 12  # el reloj analógico solo tiene 12 horas

        # 60 segundos = 360°  ->  1 segundo = 6°
        angulo_segundo = segundos * 6
        # 60 minutos = 360°  ->  1 minuto = 6°, y avanza 0.1° por segundo
        angulo_minuto = minutos * 6 + segundos * 0.1
        # 12 horas = 360°  ->  1 hora = 30°, y avanza 0.5° por minuto
        angulo_hora = horas * 30 + minutos * 0.5

        return angulo_hora, angulo_minuto, angulo_segundo

    @staticmethod
    def punto(centro_x, centro_y, largo, angulo_grados):
        """Punto a 'largo' píxeles del centro, en la dirección del ángulo.

        En la pantalla la Y crece hacia abajo, por eso se RESTA el coseno.
        """
        x = centro_x + largo * seno(angulo_grados)
        y = centro_y - largo * coseno(angulo_grados)
        return x, y


# ----------------------------------------------------------------------
# 3. LÓGICA DE LA ALARMA (tampoco sabe nada de la interfaz)
# ----------------------------------------------------------------------
class Alarma:
    """Guarda la hora de la alarma y decide cuándo debe sonar."""

    def __init__(self):
        self.hora = None      # entero 0-23
        self.minuto = None    # entero 0-59
        self.activa = False

    @staticmethod
    def interpretar(texto):
        """Convierte 'HH:MM' en (hora, minuto).

        Lanza ValueError con un mensaje claro si el texto no es válido.
        """
        texto = texto.strip()
        if not texto:
            raise ValueError("Escribe una hora con el formato HH:MM.")

        partes = texto.split(":")
        if len(partes) != 2:
            raise ValueError("Usa el formato HH:MM, por ejemplo 07:30.")

        hora_txt, minuto_txt = partes
        if not (hora_txt.isdigit() and minuto_txt.isdigit()):
            raise ValueError("La hora y los minutos deben ser números.")

        hora, minuto = int(hora_txt), int(minuto_txt)
        if not 0 <= hora <= 23:
            raise ValueError("La hora debe estar entre 00 y 23.")
        if not 0 <= minuto <= 59:
            raise ValueError("Los minutos deben estar entre 00 y 59.")
        return hora, minuto

    def activar(self, texto):
        """Valida el texto y, si es correcto, activa la alarma."""
        self.hora, self.minuto = self.interpretar(texto)  # puede lanzar ValueError
        self.activa = True

    def desactivar(self):
        self.activa = False

    def debe_sonar(self, ahora):
        """True si la alarma está activa y llegó su hora y minuto."""
        return (self.activa
                and ahora.hora == self.hora
                and ahora.minuto == self.minuto)

    def texto_hora(self):
        return f"{self.hora:02d}:{self.minuto:02d}"


# ----------------------------------------------------------------------
# 4. DIBUJO DEL RELOJ (interfaz: solo dibuja)
# ----------------------------------------------------------------------
class RelojAnalogico:
    """Dibuja la esfera, los números y las manecillas en un Canvas."""

    COLOR_FONDO = "#1e2433"
    COLOR_ESFERA = "#fdfaf3"
    COLOR_BORDE = "#c9a227"
    COLOR_TEXTO = "#1e2433"
    COLOR_HORA = "#1e2433"
    COLOR_MINUTO = "#3b4a6b"
    COLOR_SEGUNDO = "#d1495b"

    def __init__(self, contenedor, tamano=320):
        self.tamano = tamano
        self.centro = tamano / 2
        self.radio = tamano / 2 - 15

        self.canvas = tk.Canvas(contenedor, width=tamano, height=tamano,
                                bg=self.COLOR_FONDO, highlightthickness=0)

        self._dibujar_esfera()
        # Las manecillas se crean una sola vez y luego solo se MUEVEN.
        self.manecilla_hora = self._crear_manecilla(7, self.COLOR_HORA)
        self.manecilla_minuto = self._crear_manecilla(4, self.COLOR_MINUTO)
        self.manecilla_segundo = self._crear_manecilla(2, self.COLOR_SEGUNDO)
        # Punto central encima de las manecillas
        c, r = self.centro, 7
        self.canvas.create_oval(c - r, c - r, c + r, c + r,
                                fill=self.COLOR_SEGUNDO, outline="")

    def _dibujar_esfera(self):
        """Dibuja la parte fija: círculo, marcas y números del 1 al 12."""
        c, r = self.centro, self.radio
        self.canvas.create_oval(c - r, c - r, c + r, c + r,
                                fill=self.COLOR_ESFERA,
                                outline=self.COLOR_BORDE, width=6)

        # 60 marcas: gruesas en las horas, delgadas en los minutos
        for i in range(60):
            angulo = i * 6
            es_hora = i % 5 == 0
            inicio = r - (16 if es_hora else 8)
            x1, y1 = LogicaReloj.punto(c, c, inicio, angulo)
            x2, y2 = LogicaReloj.punto(c, c, r - 4, angulo)
            self.canvas.create_line(x1, y1, x2, y2, fill=self.COLOR_TEXTO,
                                    width=3 if es_hora else 1)

        # Números del 1 al 12 (cada uno a 30° del anterior)
        for numero in range(1, 13):
            x, y = LogicaReloj.punto(c, c, r - 34, numero * 30)
            self.canvas.create_text(x, y, text=str(numero),
                                    font=("Helvetica", 16, "bold"),
                                    fill=self.COLOR_TEXTO)

    def _crear_manecilla(self, grosor, color):
        c = self.centro
        return self.canvas.create_line(c, c, c, c, width=grosor, fill=color,
                                       capstyle=tk.ROUND)

    def actualizar(self, ahora):
        """Mueve las tres manecillas según la hora recibida."""
        a_hora, a_minuto, a_segundo = LogicaReloj.angulos(ahora)
        c, r = self.centro, self.radio
        # (manecilla, ángulo, largo como fracción del radio)
        for manecilla, angulo, largo in (
            (self.manecilla_hora, a_hora, 0.50),
            (self.manecilla_minuto, a_minuto, 0.72),
            (self.manecilla_segundo, a_segundo, 0.82),
        ):
            x, y = LogicaReloj.punto(c, c, r * largo, angulo)
            self.canvas.coords(manecilla, c, c, x, y)


# ----------------------------------------------------------------------
# 5. APLICACIÓN (ventana principal: une reloj, alarma e interfaz)
# ----------------------------------------------------------------------
class Aplicacion:
    def __init__(self, ventana):
        self.ventana = ventana
        self.alarma = Alarma()
        self.id_tarea = None        # tarea programada con after()
        self.ventana_aviso = None   # ventana emergente de la alarma

        ventana.title("Reloj con Alarma")
        ventana.configure(bg=RelojAnalogico.COLOR_FONDO, padx=20, pady=15)
        ventana.resizable(False, False)

        self._crear_interfaz()
        # Cerrar con la X detiene el ciclo antes de destruir la ventana
        ventana.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.tic()  # arranca el ciclo de actualización

    # ---------- construcción de la interfaz ----------
    def _crear_interfaz(self):
        fondo = RelojAnalogico.COLOR_FONDO
        claro = "#fdfaf3"

        self.reloj = RelojAnalogico(self.ventana)
        self.reloj.canvas.pack()

        self.etiqueta_digital = tk.Label(self.ventana, font=("Helvetica", 18, "bold"),
                                         bg=fondo, fg=claro)
        self.etiqueta_digital.pack(pady=(8, 10))

        marco = tk.Frame(self.ventana, bg=fondo)
        marco.pack()

        tk.Label(marco, text="Alarma (HH:MM, 24 h):", bg=fondo, fg=claro,
                 font=("Helvetica", 11)).grid(row=0, column=0, padx=(0, 6))
        self.campo_alarma = tk.Entry(marco, width=7, justify="center",
                                     font=("Helvetica", 13))
        self.campo_alarma.grid(row=0, column=1)
        self.campo_alarma.bind("<Return>", lambda evento: self.activar_alarma())

        botones = tk.Frame(self.ventana, bg=fondo)
        botones.pack(pady=8)
        self.boton_activar = tk.Button(botones, text="Activar alarma", width=14,
                                       command=self.activar_alarma)
        self.boton_activar.grid(row=0, column=0, padx=4)
        self.boton_desactivar = tk.Button(botones, text="Desactivar alarma", width=14,
                                          command=self.desactivar_alarma)
        self.boton_desactivar.grid(row=0, column=1, padx=4)

        self.etiqueta_estado = tk.Label(self.ventana, font=("Helvetica", 11),
                                        bg=fondo, wraplength=320)
        self.etiqueta_estado.pack()
        self.mostrar_estado("Alarma desactivada", "#aab3c5")

    def mostrar_estado(self, texto, color):
        self.etiqueta_estado.config(text=texto, fg=color)

    # ---------- acciones de los botones ----------
    def activar_alarma(self):
        try:
            self.alarma.activar(self.campo_alarma.get())
        except ValueError as error:
            # Entrada inválida: se informa y la alarma queda como estaba
            self.mostrar_estado(f"Error: {error}", "#ff8a80")
            return
        self.mostrar_estado(f"Alarma ACTIVADA para las {self.alarma.texto_hora()}",
                            "#7ee081")

    def desactivar_alarma(self):
        self.alarma.desactivar()
        self.cerrar_aviso()
        self.mostrar_estado("Alarma desactivada", "#aab3c5")

    # ---------- ciclo de actualización ----------
    def tic(self):
        """Se ejecuta una vez por segundo: actualiza reloj y revisa alarma."""
        ahora = Hora.actual(self.ventana)
        self.reloj.actualizar(ahora)
        self.etiqueta_digital.config(text=ahora.texto())

        if self.alarma.debe_sonar(ahora):
            self.disparar_alarma()

        # Programar el siguiente tic justo al inicio del próximo segundo
        espera = 1000 - ahora.milisegundo
        self.id_tarea = self.ventana.after(espera, self.tic)

    def disparar_alarma(self):
        hora = self.alarma.texto_hora()
        self.alarma.desactivar()  # suena una sola vez
        self.mostrar_estado(f"¡La alarma de las {hora} sonó!", "#ffd166")
        self.ventana.bell()       # pitido del sistema
        self.mostrar_aviso(hora)

    def mostrar_aviso(self, hora):
        """Ventana emergente que NO bloquea el reloj."""
        self.cerrar_aviso()
        aviso = tk.Toplevel(self.ventana)
        aviso.title("¡Alarma!")
        aviso.configure(bg=RelojAnalogico.COLOR_SEGUNDO, padx=30, pady=20)
        aviso.transient(self.ventana)
        # Ubicar el aviso encima del reloj
        aviso.geometry(f"+{self.ventana.winfo_rootx() + 60}"
                       f"+{self.ventana.winfo_rooty() + 100}")
        tk.Label(aviso, text="¡ALARMA!", font=("Helvetica", 22, "bold"),
                 bg=RelojAnalogico.COLOR_SEGUNDO, fg="white").pack()
        tk.Label(aviso, text=f"Son las {hora}", font=("Helvetica", 14),
                 bg=RelojAnalogico.COLOR_SEGUNDO, fg="white").pack(pady=8)
        tk.Button(aviso, text="Aceptar", width=10,
                  command=self.cerrar_aviso).pack()
        aviso.protocol("WM_DELETE_WINDOW", self.cerrar_aviso)
        self.ventana_aviso = aviso

    def cerrar_aviso(self):
        if self.ventana_aviso is not None:
            self.ventana_aviso.destroy()
            self.ventana_aviso = None

    def cerrar(self):
        """Cancela la tarea pendiente y cierra sin errores."""
        if self.id_tarea is not None:
            self.ventana.after_cancel(self.id_tarea)
            self.id_tarea = None
        self.ventana.destroy()


# ----------------------------------------------------------------------
# Punto de entrada
# ----------------------------------------------------------------------
def main():
    ventana = tk.Tk()
    Aplicacion(ventana)
    ventana.mainloop()


if __name__ == "__main__":
    main()