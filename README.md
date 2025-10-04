# Calificador OnlineGDB

Este proyecto permite **calificar automáticamente** entregas exportadas en formato `.csv` desde [OnlineGDB](https://www.onlinegdb.com/) y generar un archivo consolidado con todas las notas de los estudiantes.  

## 🚀 Funcionalidades

- Lee archivos `.csv` exportados desde OnlineGDB.
- Normaliza fechas y horas de entrega.
- Calcula la nota de cada estudiante en base a:
  - Número de pruebas pasadas vs. total de pruebas.
  - Penalización por entregas tardías (según `due_dates.json`).
  - Curva ajustable de calificación (`k`).
- Genera archivos `.csv` con las notas individuales de cada tarea (en la carpeta `graded/`).
- Consolida todas las notas en un único archivo `notes.csv`.

## Estructura del repositorio

```bash
├── exports/          # Carpeta con los .csv crudos exportados desde OnlineGDB
├── graded/           # Carpeta donde se guardan los .csv ya calificados
├── due_dates.json    # Fechas de entrega de cada tarea
├── main.py           # Script principal
└── notes.csv         # Consolidado de todas las notas (generado automáticamente)
```

## ⚙️ Uso

1. Coloca los archivos exportados de OnlineGDB en la carpeta `exports/`.
2. Crea un archivo `due_dates.json` las llaves son el nombre de los archivos y el valor son las fechas de entrega.
3. Ejecuta el script principal:

```bash
python main.py
```

4. Se generarán:
   - Archivos `.csv` calificados en `graded/`.
   - Un archivo `notes.csv` con el consolidado de todas las notas.

## 📊 Ejemplo de calificación

- Nota máxima: **5.0**
- Nota mínima: **0.0**
- Penalización por entrega tardía: **-0.5**.
- Curva ajustable (`k`):
  - `k < 1`: más generoso.
  - `k = 1`: lineal.
  - `k > 1`: más estricto.

## 🛠️ Requisitos

- Python 3.8+
- Librerías:
  - `pandas`
  - `numpy`

Instalación rápida:

```bash
pip install pandas numpy
```
