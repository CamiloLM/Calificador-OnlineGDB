import glob
import json
import os
import re
from datetime import datetime
from math import floor

import pandas as pd


class Assignment:
    """Objeto para calcular las tareas de OnlineGDB"""

    def __init__(self, path: str):
        """
        Inicializa el objeto cargando un archivo tipo csv en la ubicación indicada por path
        Se guardan los datos en un data frame de pandas para modificarlos facilmente
        """
        self._path = path
        self._df = pd.read_csv(path, encoding="utf-8", sep=",")
        self._df["Grade"] = self._df["Grade"].astype(float)
        self.clean_dates()

    def __str__(self):
        return self._df.head().to_string(index=False)

    @property
    def df(self):
        return self._df

    @property
    def path(self):
        return self._path

    def clean_dates(self):
        """
        Normaliza las fechas y crea una nueva columna Submission Hour.
        """
        # El regex funciona de alguna forma
        extracted = self.df["Submission Date"].str.extract(
            r"(?P<date>\d{1,2}/\d{1,2}/\d{4}),\s+(?P<hour>\d{1,2}:\d{2}:\d{2}\s+[APM]{2})"
        )

        self.df["Submission Date"] = extracted["date"]
        self.df["Submission Hour"] = extracted["hour"]

    def calculate_penalty(self, sub_dt):
        name = self.get_assignment_name()
        date_str = ""
        with open("due_dates.json", "r") as file:
            data = json.load(file)
            for key, value in data.items():
                if name == key:
                    date_str = value
            if not date_str:
                raise ValueError(
                    "La asignacion no tiene fecha asignada en el archivo .json"
                )

        due_dt = datetime.strptime(date_str, "%m/%d/%Y %I:%M %p")

        if sub_dt <= due_dt:
            return 0
        else:
            delta = sub_dt - due_dt
            penalty = 0.5
            if delta.days > 0:
                # TODO: Interpretacion diferente de las 12 hroas
                extra_hours = (delta.days - 1) * 24 + delta.seconds // 3600
                penalty += (extra_hours // 12) * 0.5
            return penalty

    def calculate_grade(
        self, result: str, date: str, time: str, k: float = 0.8
    ) -> float:
        """
        Calcula la nota de un estudiante a partir de los resultados de las pruebas.
        - Máxima nota: 5.0 (todas las pruebas se pasaron)
        - Nota mínima: 0.0 (no paso ninguna prueba o dio error de compilación)
        - Penalización por entrega tardía: -0.5
        - Escala de curva por parámetro k (0.5 generoso, 1 lineal, 2 duro)
        """
        if result.strip().lower() == "compile error":
            return 0.0

        passed, total = map(int, re.findall(r"\d+", result))

        if passed > 0:
            f = passed / total if total > 0 else 0
            grade = 5 * (f**k)
        else:
            grade = 0.0

        date_obj = datetime.strptime(date, "%m/%d/%Y").date()
        time_obj = datetime.strptime(time, "%I:%M:%S %p").time()

        due_dt = datetime.combine(date_obj, time_obj)
        penalty = self.calculate_penalty(due_dt)
        grade -= penalty
        return floor(grade)
        # return round(grade * 2) / 2

    def grade_students(self):
        """Calcula la nota de todos los estudiantes según calculate_grade y lo guarda en el data frame"""
        for i, row in self.df.iterrows():
            grade = self.calculate_grade(
                row["Test Result"], row["Submission Date"], row["Submission Hour"]
            )
            self.df.loc[i, "Grade"] = grade

    def get_assignment_name(self):
        """Retorna el nombre el archivo que debería ser el nombre de la tarea"""
        base = os.path.basename(self._path)
        name, _ = os.path.splitext(base)
        return name

    def get_students(self):
        """Devuelve una lista con los nombres de estudiantes que hicieron la entrega"""
        return self._df["Submitted By"].dropna().unique().tolist()

    def get_grade_by_name(self, student_name: str):
        """Devuelve la nota que saco el estudiante"""
        matches = self._df.index[self._df["Submitted By"] == student_name]
        if len(matches) > 0:
            return float(self._df.at[matches[0], "Grade"])
        return 0

    def save_assingment(self, output_dir: str):
        """
        Crea un documento .csv en el que guarda el data table de la tarea.
        Las tareas se guardan en el directorio especificado
        """
        os.makedirs(output_dir, exist_ok=True)

        # Crea el nombre del documento
        base = os.path.basename(self._path)
        name, ext = os.path.splitext(base)
        new_name = f"{name}_graded{ext}"

        # Crea el path
        output_path = os.path.join(output_dir, new_name)

        # Guarda como CSV
        self._df.to_csv(output_path, index=False, encoding="utf-8")
        print(f" Archivo guardado en {output_path}")


class Notes:
    """Clase para almacenar todas las notas en un solo archivo"""

    def __init__(self, folder: str):
        """
        Inicializa el objeto con los archivos que se encuentran la carpeta especificada,
        se espera que los archivos .csv hayan sido instanciados por la clase Assignment
        """
        self._folder = folder
        self._df_list = []

    @property
    def df_list(self):
        return self._df_list

    def sort_order(self, s: str):
        """Ordenamiento de las tares primero por número luego por nombre"""
        return [
            int(text) if text.isdigit() else text.lower()
            for text in re.split(r"(\d+)", s)
        ]

    def load_assignments(self):
        """Carga todos los archivos .csv en la carpeta dada al constructor"""
        pattern = os.path.join(self._folder, "*.csv")
        files = glob.glob(pattern)

        self._df_list = [Assignment(f) for f in files]
        self._df_list.sort(key=lambda a: self.sort_order(a.get_assignment_name()))

        print(f"Cargadas {len(self._df_list)} tareas de {self._folder}")
        return self._df_list

    def save_notes(self, file_name):
        """Guarda todas las notas en un solo archivo file_name.csv"""
        # Buscar todos los nombres de los estudiantes
        all_students = set()
        for assignment in self._df_list:
            all_students.update(assignment.get_students())

        # Crea nuevo data frame con todas las notas
        notes_df = pd.DataFrame({"Nombre": sorted(all_students)})

        for assignment in self._df_list:
            col_name = assignment.get_assignment_name()
            notes_df[col_name] = notes_df["Nombre"].apply(
                lambda student: assignment.get_grade_by_name(student)
            )

        output_path = os.path.join(os.getcwd(), file_name)
        notes_df.to_csv(output_path, index=False, encoding="utf-8")

        print(f"Notas guardadas en {output_path}")


if __name__ == "__main__":
    # Carga los archivos .csv en exports/ en una lista
    folder = "exports/"
    csv_paths = [
        os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".csv")
    ]
    assignments = [Assignment(path) for path in csv_paths]

    # Recorre la lista de las tareas, las califica y las guarda en la carpeta graded/
    for a in assignments:
        a.grade_students()
        a.save_assingment("graded")

    # Carga todas las notas calificadas en la carpeta graded/ y las guarda en el archivo notes.csv
    notes = Notes("graded")
    notes.load_assignments()
    notes.save_notes("notes.csv")

    # Recorre todas las notas que estan en la clase Notes y muestra los primeros 5 resultados
    for a in notes.df_list:
        print("\n----------------------------")
        print(a.get_assignment_name())
        print(a)
