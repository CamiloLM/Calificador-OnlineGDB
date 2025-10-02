import glob
import os
import re

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
        """Corrige la celda para que no tenga saltos de linea o espacios adiconales"""
        self.df["Submission Date"] = (
            self.df["Submission Date"]
            .str.replace("\n", "", regex=False)
            .str.strip()
            .str.replace(r"\s+\(late submission\)", " (late submission)", regex=True)
        )

    def calculate_grade(
        self, result: str, submission_date: str, k: float = 0.8
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

        passed, total = map(int,re.findall(r"\d+", result))

        if passed > 0:
            f = passed / total if total > 0 else 0
            grade = 5 * (f**k)
        else:
            grade = 0.0

        # TODO: Hay que quitar 0.5 si se hace el mismo dia de la clase
        # si pasa mas de un dia hay que quitar 0.5 cada 12 horas
        # if "(late submission)" in submission_date:
        #     grade -= 0.5

        return round(grade * 2) / 2

    def grade_students(self):
        """Calcula la nota de todos los estudiantes según calculate_grade y lo guarda en el data frame"""
        for i, row in self.df.iterrows():
            grade = self.calculate_grade(row["Test Result"], row["Submission Date"])
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
        """Guarda todas las notas en un solo archivo .csv"""
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

        if os.path.exists(output_path):
            choice = input(
                f"El achivo {file_name} ya existe. Desea reemplazarlo? (Y/N): "
            )
            if choice.lower != "y":
                print("El archivo no fue reemplazado")
                return

        notes_df.to_csv(output_path, index=False, encoding="utf-8")
        print(f"Notas guardadas en {output_path}")


if __name__ == "__main__":
    # Para una sola tarea
    a_path = "./exports/8_Corchetes_Balanceados.csv"
    a = Assignment(a_path)
    a.grade_students()
    print(a)  # Imprime las primeras 5 notas
    a.save_assingment("graded")

    # Para todas las notas
    notes = Notes("graded/")
    notes.load_assignments()

    for a in notes.df_list:
        print("----")
        print(a.get_assignment_name())
        print(a)

    # a.save_assingment("graded")

    # Probar la funcion de calcular las notas
    # b = Assignment.__new__(Assignment)

    # test_cases = [
    #     ("Compile error", "9/22/2025, 7:12:41 AM"),
    #     ("1 passed of 1", "9/22/2025, 7:12:41 AM"),
    #     ("1 passed of 2", "9/22/2025, 7:12:41 AM"),
    #     ("2 passed of 2", "9/22/2025, 7:12:41 AM"),
    #     ("2 passed of 3", "9/22/2025, 7:12:41 AM"),
    #     ("4 passed of 6", "9/22/2025, 7:12:41 AM"),
    #     ("1 passed of 6", "9/22/2025, 7:12:41 AM"),
    #     ("0 passed of 6", "9/22/2025, 7:12:41 AM"),
    #     ("3 passed of 6", "9/22/2025, 7:12:41 AM"),
    #     ("2 passed of 3", "9/22/2025, 7:12:41 AM (late submission)"),
    # ]

    # for result, date in test_cases:
    #     grade = b.calculate_grade(result, date)
    #     print(
    #         f"Result: {result:20} | Date: {date:30} | Grade: {grade}"
    #     )
