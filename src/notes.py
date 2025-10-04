import os
import re
from glob import glob

import pandas as pd

from src.assignment import Assignment


class Notes:
    """Clase para almacenar todas las notas en un solo archivo"""

    def __init__(self, folder: str):
        """
        Inicializa el objeto con los archivos que se encuentran la carpeta especificada,
        se espera que los archivos .csv hayan sido instanciados por la clase Assignment
        """
        self._folder = folder
        self._df_list = []
        self._load_assignments()

    @property
    def df_list(self):
        return self._df_list

    @df_list.setter
    def df_list(self, new_list):
        self._df_list = new_list

    def _sort_order(self, s: str):
        """Ordenamiento de las asignaciones primero por número luego por nombre."""
        return [
            int(text) if text.isdigit() else text.lower()
            for text in re.split(r"(\d+)", s)
        ]

    def _load_assignments(self) -> None:
        """
        Carga todos los archivos .csv en la carpeta dada al constructor."""
        pattern = os.path.join(self._folder, "*.csv")
        files = glob(pattern)

        self.df_list = [Assignment(f) for f in files]
        self.df_list.sort(key=lambda a: self._sort_order(a.name()))

        print(f"Se cargaron {len(self.df_list)} tareas de {self._folder}")

    def save_notes(self, file_name):
        """Guarda todas las notas en un solo archivo"""

        # Buscar todos los nombres de los estudiantes
        all_students = set()
        for assignment in self.df_list:
            all_students.update(assignment.get_all_students())

        # Crea nuevo data frame para almacenar todas las notas
        notes_df = pd.DataFrame({"Nombre": sorted(all_students)})

        # Crea las columnas con el nombre de la asignación y agrega las notas como filas
        for assignment in self.df_list:
            col_name = assignment.name()
            notes_df[col_name] = notes_df["Nombre"].apply(
                lambda student: assignment.get_student_grade(student)
            )

        output_path = os.path.join(os.getcwd(), file_name)
        notes_df.to_csv(output_path, index=False, encoding="utf-8")

        print(f"Notas guardadas en {output_path}")
