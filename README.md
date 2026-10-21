# Reloj con Alarma en Python

Proyecto de Estructuras de Datos — «Desarrollo de un Reloj con Python».

## Descripción

Aplicación de escritorio que muestra un **reloj analógico** (esfera, números del 1 al 12 y manecillas de horas, minutos y segundos) que se actualiza cada segundo con la hora del computador. Debajo muestra la hora en formato digital.

**Funcionalidad adicional: alarma.** El usuario escribe una hora (HH:MM, formato 24 h), la activa o desactiva con dos botones y ve siempre el estado de la alarma. Cuando llega la hora suena un pitido del sistema y aparece una ventana de aviso, sin detener el reloj.

Está hecha con **código Python puro**. La única importación es `tkinter`, el módulo que trae Python para crear ventanas; sin él, la única forma de hacer una interfaz sería HTML/CSS, que está prohibido. Todo lo demás es código propio: el seno y el coseno se calculan con series de Taylor (sin `math`) y la hora se lee del sistema a través de la propia ventana (sin `datetime`). No usa HTML, CSS, JavaScript ni frameworks web, y no requiere instalar nada.

## Archivos

| Archivo | Contenido |
|---|---|
| `reloj_alarma.py` | Programa completo |
| `README.md` | Este documento |

## Requisitos

- Python 3.8 o superior (con Tkinter, que viene incluido en el instalador oficial de python.org para Windows y macOS).

## Cómo ejecutar

Abrir una terminal en la carpeta del proyecto y ejecutar:

```
python reloj_alarma.py
```

(En Windows también funciona `py reloj_alarma.py`; en macOS/Linux puede ser `python3 reloj_alarma.py`.)

## Cómo usar la alarma

1. Escribir la hora en el campo, por ejemplo `07:30` o `19:05`.
2. Pulsar **Activar alarma** (o la tecla Enter).
3. El mensaje verde confirma la hora programada.
4. **Desactivar alarma** la cancela.
5. A la hora programada aparece el aviso «¡ALARMA!»; se cierra con **Aceptar**.

## Limitaciones

- La alarma es de una sola vez: después de sonar queda desactivada.
- Solo una alarma a la vez.
- El sonido es el pitido del sistema; en algunos equipos puede estar silenciado (el aviso visual siempre aparece).
- La alarma no se guarda al cerrar el programa.