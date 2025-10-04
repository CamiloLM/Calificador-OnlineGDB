import json
import os
import re
from datetime import datetime, timedelta
from math import floor
from typing import List

import pandas as pd


class Assignment:
    """Calcular las asignaciones de OnlineGDB"""

    def __init__(self, path: str):
        """
        Inicializa el objeto cargando un archivo tipo csv en la ubicación indicada por path.
        """
        self._path = path
        self._df = pd.read_csv(path, encoding="utf-8", sep=",")
        self._df["Grade"] = self._df["Grade"].astype(float)
        self._clean_dates()

    def __str__(self):
        return self._df.to_string(index=False)

    @property
    def df(self):
        return self._df

    @property
    def path(self):
        return self._path

    def _clean_dates(self) -> None:
        """
        Normaliza las fechas y las separa de las horas.
        """
        pattern = r"(?P<date>\d{1,2}/\d{1,2}/\d{4}),\s+(?P<hour>\d{1,2}:\d{2}:\d{2}\s+[APM]{2})"

        # Crea un data frame con los grupos como columnas
        extracted = self.df["Submission Date"].str.extract(pattern)

        self.df["Submission Date"] = extracted["date"]
        self.df["Submission Hour"] = extracted["hour"]

    def grade_students(self) -> None:
        """Calcula la nota de todos los estudiantes."""
        self.df["Grade"] = self.df.apply(
            lambda row: self._calculate_note(
                row["Test Result"], row["Submission Date"], row["Submission Hour"]
            ),
            axis=1,
        )

    def _calculate_note(
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

        sub_dt = datetime.combine(date_obj, time_obj)
        penalty = self._calculate_penalty(sub_dt)
        grade -= penalty
        return floor(grade)

    def _calculate_penalty(self, sub_dt) -> float:
        name = self.name()

        with open("due_dates.json", "r") as file:
            data = json.load(file)

        due_str = data.get(name)

        if not due_str:
            raise ValueError(f"La asignacion {name} no tiene fecha en due_dates.json")

        due_dt = datetime.strptime(due_str, "%m/%d/%Y %I:%M %p")

        # Caso 1: Entregado a tiempo
        if sub_dt <= due_dt:
            return 0.0
        # Caso 2: Entregado tarde pero el mismo día
        elif sub_dt.date() == due_dt.date():
            return 0.5
        # Caso 3: Entregado días después
        else:
            midnight = datetime.combine(
                due_dt.date() + timedelta(days=1), datetime.min.time()
            )
            hours_late = (sub_dt - midnight).total_seconds() // 3600

            return 0.5 + (hours_late // 12) * 0.5

    def name(self) -> str:
        """Retorna el nombre el archivo que debería ser el nombre de la tarea"""
        base = os.path.basename(self.path)
        name, _ = os.path.splitext(base)
        return name

    def get_all_students(self) -> List[str]:
        """Devuelve una lista con los nombres de estudiantes que hicieron la entrega"""
        return self.df["Submitted By"].dropna().unique().tolist()

    def get_student(self, student_name: str) -> pd.DataFrame:
        """Devuelve una lista con los nombres de estudiantes que hicieron la entrega"""
        return self.df.loc[self.df["Submitted By"] == student_name]

    def get_student_grade(self, student_name: str) -> float:
        """Devuelve la nota que saco el estudiante, si el estudiante no presento la tarea la nota es 0"""
        matches = self._df.index[self._df["Submitted By"] == student_name]
        # TODO: Caso si hay dos estudiantes con el mismo nombre
        if len(matches) > 0:
            return float(self._df.at[matches[0], "Grade"])
        return 0.0

    def save_assignment(self, output_dir: str) -> None:
        """
        Crea un documento .csv con el nombre de la tarea y lo guarda en el directorio especificado.
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
