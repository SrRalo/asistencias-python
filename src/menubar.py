from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QLabel, QComboBox, QPushButton, 
    QTableWidget, QTableWidgetItem, QWidget, QFileDialog, 
    QMessageBox, QLineEdit, QDateEdit, QTimeEdit, QTextEdit
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QDate, QTime, Qt
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from io import BytesIO
from conexion import (
    query_with_joins, query_data, connect_to_db, register_data, 
    execute_query, join_tables, check_if_exists, buscar_datos
)
from psycopg2.extras import RealDictCursor
import os

#Administrar Usuarios
class AdminUsuariosWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Administrador de Usuarios")
        self.setGeometry(100, 100, 800, 600)

        # Layout principal
        layout = QtWidgets.QVBoxLayout(self)

        # Label del título
        self.title_label = QtWidgets.QLabel("ADMINISTRADOR DE USUARIOS")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)

        # Formulario para ingresar usuario, clave y rol
        form_layout = QtWidgets.QFormLayout()
        self.user_input = QtWidgets.QLineEdit()
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.role_input = QtWidgets.QComboBox()
        self.role_input.addItems(["Estudiante", "Docente", "Tutor", "Admin"])  # Opciones de rol
        form_layout.addRow("Usuario:", self.user_input)
        form_layout.addRow("Clave:", self.password_input)
        form_layout.addRow("Rol:", self.role_input)

        # Botones de acción
        self.save_button = QtWidgets.QPushButton("Guardar")
        self.delete_button = QtWidgets.QPushButton("Eliminar")
        self.search_button = QtWidgets.QPushButton("Buscar")
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)

        # Tabla de usuarios
        self.user_table = QtWidgets.QTableWidget()
        self.user_table.setColumnCount(3)
        self.user_table.setHorizontalHeaderLabels(["Usuario", "Clave", "Rol"])
        self.user_table.horizontalHeader().setStretchLastSection(True)

        # Agregar al layout principal
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        layout.addWidget(self.user_table)

        # Conectar botones con funciones
        self.save_button.clicked.connect(self.save_user)
        self.delete_button.clicked.connect(self.delete_user)
        self.search_button.clicked.connect(self.search_user)

        # Cargar usuarios al iniciar
        self.load_users()

    def save_user(self):
        import conexion
        usuario = self.user_input.text()
        clave = self.password_input.text()
        rol = self.role_input.currentText()

        if usuario and clave and rol:
            data = {
                "Nombre_Usuario": usuario,
                "Clave": clave,
                "Rol": rol
            }
            conexion.register_data("Usuario", data)
            self.load_users()
            QtWidgets.QMessageBox.information(self, "Éxito", "Usuario guardado correctamente.")
        else:
            QtWidgets.QMessageBox.warning(self, "Advertencia", "Por favor completa todos los campos.")

    def delete_user(self):
        import conexion
        usuario = self.user_input.text()

        if usuario:
            exists = conexion.check_if_exists(
                "SELECT COUNT(*) FROM Usuario WHERE Nombre_Usuario = %s", (usuario,)
            )
            if exists:
                query = "DELETE FROM Usuario WHERE Nombre_Usuario = %s"
                conn = conexion.connect_to_db()
                with conn.cursor() as cursor:
                    cursor.execute(query, (usuario,))
                    conn.commit()
                QtWidgets.QMessageBox.information(self, "Éxito", "Usuario eliminado correctamente.")
                self.load_users()
            else:
                QtWidgets.QMessageBox.warning(self, "Advertencia", "Usuario no encontrado.")
        else:
            QtWidgets.QMessageBox.warning(self, "Advertencia", "Por favor ingresa un nombre de usuario.")

    def search_user(self):
        """
        Busca usuarios en la tabla 'Usuario' según el texto ingresado en el campo de usuario.
        """
        from conexion import buscar_datos

        consulta = self.user_input.text().strip()

        if consulta:
            try:
                # Llama a la función buscar_datos para obtener resultados
                usuarios = buscar_datos("Usuario", "Nombre_Usuario", consulta)
                if usuarios:
                    self.populate_user_table(usuarios)
                    QtWidgets.QMessageBox.information(self, "Resultados", f"Se encontraron {len(usuarios)} coincidencias.")
                else:
                    QtWidgets.QMessageBox.warning(self, "Sin resultados", "No se encontraron coincidencias.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Ocurrió un error al buscar usuarios: {e}")
        else:
            QtWidgets.QMessageBox.warning(self, "Advertencia", "Por favor, ingresa un nombre de usuario para buscar.")


    def load_users(self):
        import conexion
        users = conexion.query_data("Usuario")
        self.populate_user_table(users)

    def populate_user_table(self, users):
        self.user_table.setRowCount(0)  # Limpiar la tabla
        for row_num, user in enumerate(users):
            self.user_table.insertRow(row_num)
            self.user_table.setItem(row_num, 0, QtWidgets.QTableWidgetItem(user[0]))  # Nombre_Usuario
            self.user_table.setItem(row_num, 1, QtWidgets.QTableWidgetItem(user[1]))  # Clave
            self.user_table.setItem(row_num, 2, QtWidgets.QTableWidgetItem(user[2]))  # Rol

#Registrar Docente
class RegistrarDocenteWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar Docente")
        self.setGeometry(100, 100, 400, 350)  # Aumenté el tamaño de la ventana

        # Crear un QLabel para la imagen de fondo
        self.label_image = QLabel(self)
        self.label_image.setGeometry(0, 0, self.width(), self.height())

        # Construir la ruta relativa de la imagen
        image_path = os.path.join(os.path.dirname(os.getcwd()), "IngresoUsuarios.jpg")
        if not os.path.exists(image_path):
            print(f"Error: La imagen no existe en la ruta: {image_path}")
        else:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print("Error: La imagen no se cargó correctamente.")
            else:
                # Ajustar la imagen al tamaño del QLabel manteniendo la proporción
                self.label_image.setPixmap(pixmap.scaled(
                    self.label_image.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))

        self.label_image.setAlignment(Qt.AlignCenter)
        self.label_image.lower()  # Asegurarse de que la imagen quede detrás de los widgets

        # Crear el layout principal
        layout = QVBoxLayout()

        # Campos del formulario
        self.label_id_docente = QLabel("ID del Docente:")
        self.input_id_docente = QLineEdit()
        layout.addWidget(self.label_id_docente)
        layout.addWidget(self.input_id_docente)

        self.label_nombre = QLabel("Nombre del Docente:")
        self.input_nombre = QLineEdit()
        layout.addWidget(self.label_nombre)
        layout.addWidget(self.input_nombre)

        self.label_apellido = QLabel("Apellido del Docente:")
        self.input_apellido = QLineEdit()
        layout.addWidget(self.label_apellido)
        layout.addWidget(self.input_apellido)

        self.label_correo = QLabel("Correo del Docente:")
        self.input_correo = QLineEdit()
        layout.addWidget(self.label_correo)
        layout.addWidget(self.input_correo)

        self.label_telefono = QLabel("Teléfono del Docente:")
        self.input_telefono = QLineEdit()
        layout.addWidget(self.label_telefono)
        layout.addWidget(self.input_telefono)

        # Botón para guardar
        self.button_guardar = QPushButton("Registrar")
        self.button_guardar.clicked.connect(self.guardar_docente)
        layout.addWidget(self.button_guardar)

        # Configurar el contenedor
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def resizeEvent(self, event):
        # Reajustar la imagen de fondo al redimensionar la ventana
        image_path = os.path.join(os.path.dirname(os.getcwd()), "asistencias", "IngresoUsuarios.jpeg")
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.label_image.setPixmap(pixmap.scaled(
                self.label_image.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        super().resizeEvent(event)

    def guardar_docente(self):
        # Obtener los datos del formulario
        id_docente = self.input_id_docente.text().strip()  # Obtener el ID del docente
        nombre = self.input_nombre.text().strip()
        apellido = self.input_apellido.text().strip()
        correo = self.input_correo.text().strip()
        telefono = self.input_telefono.text().strip()

        # Validar los campos obligatorios
        if not id_docente:
            QMessageBox.warning(self, "Advertencia", "El campo 'ID Docente' es obligatorio.")
            return
        if not nombre:
            QMessageBox.warning(self, "Advertencia", "El campo 'Nombre' es obligatorio.")
            return

        # Crear un diccionario con los datos del docente
        datos_docente = {
            "ID_Docente": id_docente,
            "Nombre_Docente": nombre,
            "Apellido_Docente": apellido,
            "Correo_Docente": correo,
            "Telefono_Docente": telefono,
        }

        try:
            # Llamar a la función register_data para guardar en la base de datos
            register_data("Docente", datos_docente)  # Asegúrate de que la función `register_data` maneje `ID_Docente`
            QMessageBox.information(self, "Éxito", "Docente registrado correctamente.")
            # Limpiar los campos del formulario
            self.input_id_docente.clear()
            self.input_nombre.clear()
            self.input_apellido.clear()
            self.input_correo.clear()
            self.input_telefono.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al guardar: {e}")

#Registrar Estudiante
class RegistrarEstudianteWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar Estudiante")
        self.setGeometry(100, 100, 400, 300)

        # Crear un QLabel para la imagen de fondo
        self.label_image = QLabel(self)
        self.label_image.setGeometry(0, 0, self.width(), self.height())

        # Construir la ruta relativa de la imagen
        image_path = os.path.join(os.path.dirname(os.getcwd()), "IngresoUsuarios.jpg")
        if not os.path.exists(image_path):
            print(f"Error: La imagen no existe en la ruta: {image_path}")
        else:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print("Error: La imagen no se cargó correctamente.")
            else:
                # Ajustar la imagen al tamaño del QLabel manteniendo la proporción
                self.label_image.setPixmap(pixmap.scaled(
                    self.label_image.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))

        self.label_image.setAlignment(Qt.AlignCenter)
        self.label_image.lower()  # Asegurarse de que la imagen quede detrás de los widgets

        # Crear el layout principal
        layout = QVBoxLayout()

        # Campo para el ID del estudiante
        self.label_id = QLabel("ID del Estudiante:")
        self.input_id = QLineEdit()
        layout.addWidget(self.label_id)
        layout.addWidget(self.input_id)

        # Campos del formulario
        self.label_nombre = QLabel("Nombre del Estudiante:")
        self.input_nombre = QLineEdit()
        layout.addWidget(self.label_nombre)
        layout.addWidget(self.input_nombre)

        self.label_telefono = QLabel("Teléfono del Estudiante:")
        self.input_telefono = QLineEdit()
        layout.addWidget(self.label_telefono)
        layout.addWidget(self.input_telefono)

        self.label_correo = QLabel("Correo del Estudiante:")
        self.input_correo = QLineEdit()
        layout.addWidget(self.label_correo)
        layout.addWidget(self.input_correo)

        # Botón para guardar
        self.button_guardar = QPushButton("Registrar")
        self.button_guardar.clicked.connect(self.guardar_estudiante)
        layout.addWidget(self.button_guardar)

        # Configurar el contenedor
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def guardar_estudiante(self):
        # Obtener los datos del formulario
        id_estudiante = self.input_id.text().strip()
        nombre = self.input_nombre.text().strip()
        telefono = self.input_telefono.text().strip()
        correo = self.input_correo.text().strip()

        # Validar los campos obligatorios
        if not id_estudiante or not nombre:
            QMessageBox.warning(self, "Advertencia", "Los campos 'ID' y 'Nombre' son obligatorios.")
            return

        # Crear un diccionario con los datos del estudiante
        datos_estudiante = {
            "id_estudiante": id_estudiante,
            "Nombre_Estudiante": nombre,
            "Telefono_Estudiante": telefono,
            "Correo_Estudiante": correo,
        }

        try:
            # Llamar a la función register_data para guardar en la base de datos
            register_data("Estudiante", datos_estudiante)
            QMessageBox.information(self, "Éxito", "Estudiante registrado correctamente.")

            # Limpiar los campos del formulario
            self.input_id.clear()
            self.input_nombre.clear()
            self.input_telefono.clear()
            self.input_correo.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al guardar: {e}")

#Registrar Tutor
class RegistrarTutorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar Tutor")
        self.setGeometry(100, 100, 400, 400)

        # Crear un QLabel para la imagen de fondo
        self.label_image = QLabel(self)
        self.label_image.setGeometry(0, 0, self.width(), self.height())

        # Construir la ruta relativa de la imagen
        image_path = os.path.join(os.path.dirname(os.getcwd()), "IngresoUsuarios.jpg")
        if not os.path.exists(image_path):
            print(f"Error: La imagen no existe en la ruta: {image_path}")
        else:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print("Error: La imagen no se cargó correctamente.")
            else:
                # Ajustar la imagen al tamaño del QLabel manteniendo la proporción
                self.label_image.setPixmap(pixmap.scaled(
                    self.label_image.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))

        self.label_image.setAlignment(Qt.AlignCenter)
        self.label_image.lower()  # Asegurarse de que la imagen quede detrás de los widgets

        # Crear el layout principal
        layout = QVBoxLayout()

        # Campo para el ID del tutor
        self.label_id = QLabel("ID del Tutor:")
        self.input_id = QLineEdit()
        layout.addWidget(self.label_id)
        layout.addWidget(self.input_id)

        # Campos del formulario
        self.label_nombre = QLabel("Nombre del Tutor:")
        self.input_nombre = QLineEdit()
        layout.addWidget(self.label_nombre)
        layout.addWidget(self.input_nombre)

        self.label_apellido = QLabel("Apellido del Tutor:")
        self.input_apellido = QLineEdit()
        layout.addWidget(self.label_apellido)
        layout.addWidget(self.input_apellido)

        self.label_correo = QLabel("Correo del Tutor:")
        self.input_correo = QLineEdit()
        layout.addWidget(self.label_correo)
        layout.addWidget(self.input_correo)

        self.label_telefono = QLabel("Teléfono del Tutor:")
        self.input_telefono = QLineEdit()
        layout.addWidget(self.label_telefono)
        layout.addWidget(self.input_telefono)

        # Botón para guardar
        self.button_guardar = QPushButton("Registrar")
        self.button_guardar.clicked.connect(self.guardar_tutor)
        layout.addWidget(self.button_guardar)

        # Configurar el contenedor
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def guardar_tutor(self):
        # Obtener los datos del formulario
        id_tutor = self.input_id.text().strip()
        nombre = self.input_nombre.text().strip()
        apellido = self.input_apellido.text().strip()
        correo = self.input_correo.text().strip()
        telefono = self.input_telefono.text().strip()

        # Validar los campos obligatorios
        if not id_tutor or not nombre:
            QMessageBox.warning(self, "Advertencia", "Los campos 'ID del Tutor' y 'Nombre' son obligatorios.")
            return

        # Crear un diccionario con los datos del tutor
        datos_tutor = {
            "id_tutor": id_tutor,
            "Nombre_Tutor": nombre,
            "Apellido_Tutor": apellido,
            "Correo_Tutor": correo,
            "Telefono_Tutor": telefono,
        }

        try:
            # Llamar a la función register_data para guardar en la base de datos
            register_data("Tutor", datos_tutor)
            QMessageBox.information(self, "Éxito", "Tutor registrado correctamente.")

            # Limpiar los campos del formulario
            self.input_id.clear()
            self.input_nombre.clear()
            self.input_apellido.clear()
            self.input_correo.clear()
            self.input_telefono.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al guardar: {e}")

#Registrar Asignatura
class RegistrarAsignaturaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar Asignatura")
        self.setGeometry(100, 100, 300, 350)  # Aumenté el tamaño de la ventana

        # Crear un QLabel para la imagen de fondo
        self.label_image = QLabel(self)
        self.label_image.setGeometry(0, 0, self.width(), self.height())

        # Construir la ruta relativa de la imagen
        image_path = os.path.join(os.path.dirname(os.getcwd()), "IngresoUsuarios.jpg")
        if not os.path.exists(image_path):
            print(f"Error: La imagen no existe en la ruta: {image_path}")
        else:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print("Error: La imagen no se cargó correctamente.")
            else:
                # Ajustar la imagen al tamaño del QLabel manteniendo la proporción
                self.label_image.setPixmap(pixmap.scaled(
                    self.label_image.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))

        self.label_image.setAlignment(Qt.AlignCenter)
        self.label_image.lower()  # Asegurarse de que la imagen quede detrás de los widgets

        layout = QVBoxLayout()

        # Label y entrada para ID de la Asignatura
        self.label_id_asignatura = QLabel("ID de la Asignatura:")
        self.input_id_asignatura = QLineEdit()
        layout.addWidget(self.label_id_asignatura)
        layout.addWidget(self.input_id_asignatura)

        # Label y entrada para Nombre de la Asignatura
        self.label_nombre = QLabel("Nombre de la Asignatura:")
        self.input_nombre = QLineEdit()
        layout.addWidget(self.label_nombre)
        layout.addWidget(self.input_nombre)

        # Label y entrada para Código de la Asignatura
        self.label_codigo = QLabel("Código:")
        self.input_codigo = QLineEdit()
        layout.addWidget(self.label_codigo)
        layout.addWidget(self.input_codigo)

        # Label y entrada para Descripción
        self.label_descripcion = QLabel("Descripción:")
        self.input_descripcion = QLineEdit()
        layout.addWidget(self.label_descripcion)
        layout.addWidget(self.input_descripcion)

        # Combobox para seleccionar el Docente
        self.label_docente = QLabel("Seleccionar Docente:")
        self.combo_docente = QComboBox()
        self.cargar_docentes()
        layout.addWidget(self.label_docente)
        layout.addWidget(self.combo_docente)

        # Botón para registrar la asignatura
        self.button_registrar = QPushButton("Registrar Asignatura")
        self.button_registrar.clicked.connect(self.guardar_asignatura)
        layout.addWidget(self.button_registrar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def cargar_docentes(self):
        # Cargar los docentes disponibles en el ComboBox
        docentes = query_data("Docente")
        for docente in docentes:
            self.combo_docente.addItem(f"{docente[1]} {docente[2]}", docente[0])  # Docente: nombre + apellido, id

    def guardar_asignatura(self):
        # Obtener los datos del formulario
        id_asignatura = self.input_id_asignatura.text().strip()  # Obtener el ID de la asignatura
        nombre = self.input_nombre.text().strip()
        codigo = self.input_codigo.text().strip()
        descripcion = self.input_descripcion.text().strip()
        id_docente = self.combo_docente.currentData()  # Obtener el ID del docente seleccionado

        # Validar que todos los campos estén llenos
        if not id_asignatura or not nombre or not codigo:
            QMessageBox.warning(self, "Advertencia", "Los campos 'ID Asignatura', 'Nombre' y 'Código' son obligatorios.")
            return

        # Crear un diccionario con los datos de la asignatura
        datos_asignatura = {
            "ID_Asignatura": id_asignatura,
            "ID_Docente": id_docente,
            "Nombre_Asignatura": nombre,
            "Codigo": codigo,
            "Descripcion": descripcion
        }

        try:
            # Llamar a la función register_data para guardar en la base de datos
            register_data("Asignatura", datos_asignatura)
            QMessageBox.information(self, "Éxito", "Asignatura registrada correctamente.")
            # Limpiar los campos del formulario
            self.input_id_asignatura.clear()
            self.input_nombre.clear()
            self.input_codigo.clear()
            self.input_descripcion.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al guardar: {e}")

#Ingresar Tutoria
class IngresarTutoriaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ingresar Tutoria")
        self.setGeometry(100, 100, 500, 400)

        # Crear un QLabel para la imagen de fondo
        self.label_image = QLabel(self)
        self.label_image.setGeometry(0, 0, self.width(), self.height())

        # Construir la ruta relativa de la imagen
        image_path = os.path.join(os.path.dirname(os.getcwd()),"imagen3.jpg")
        if not os.path.exists(image_path):
            print(f"Error: La imagen no existe en la ruta: {image_path}")
        else:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print("Error: La imagen no se cargó correctamente.")
            else:
                # Ajustar la imagen al tamaño del QLabel manteniendo la proporción
                self.label_image.setPixmap(pixmap.scaled(
                    self.label_image.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))

        self.label_image.setAlignment(Qt.AlignCenter)
        self.label_image.lower()  # Asegurarse de que la imagen quede detrás de los widgets

        # Crear el layout principal
        layout = QVBoxLayout()

        # Selección de Docente
        self.label_docente = QLabel("Seleccione el Docente:")
        self.combo_docente = QComboBox()
        self.cargar_docentes()
        layout.addWidget(self.label_docente)
        layout.addWidget(self.combo_docente)

        # Campo de Fecha
        self.label_fecha = QLabel("Fecha de la Tutoria:")
        self.input_fecha = QDateEdit()
        self.input_fecha.setCalendarPopup(True)
        self.input_fecha.setDate(QDate.currentDate())
        layout.addWidget(self.label_fecha)
        layout.addWidget(self.input_fecha)

        # Campo de Hora
        self.label_hora = QLabel("Hora de la Tutoria:")
        self.input_hora = QTimeEdit()
        self.input_hora.setTime(QTime.currentTime())
        layout.addWidget(self.label_hora)
        layout.addWidget(self.input_hora)

        # Campo de Temario
        self.label_temario = QLabel("Temario:")
        self.input_temario = QTextEdit()
        layout.addWidget(self.label_temario)
        layout.addWidget(self.input_temario)

        # Campo de Observación
        self.label_observacion = QLabel("Observación:")
        self.input_observacion = QTextEdit()
        layout.addWidget(self.label_observacion)
        layout.addWidget(self.input_observacion)

        # Botón para guardar
        self.button_guardar = QPushButton("Registrar Tutoria")
        self.button_guardar.clicked.connect(self.guardar_tutoria)
        layout.addWidget(self.button_guardar)

        # Configurar el contenedor
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def cargar_docentes(self):
        """Carga los docentes desde la base de datos y los agrega al combo box."""
        try:
            resultados = query_data("Docente")
            for docente in resultados:
                id_docente = docente[0]  # Asumiendo que ID_Docente es la primera columna
                nombre_completo = f"{docente[1]} {docente[2]}"  # Nombre y Apellido
                self.combo_docente.addItem(nombre_completo, id_docente)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la lista de docentes: {e}")

    def guardar_tutoria(self):
        """Guarda los datos de la tutoria en la base de datos."""
        # Obtener datos del formulario
        id_docente = self.combo_docente.currentData()
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        hora = self.input_hora.time().toString("HH:mm:ss")
        temario = self.input_temario.toPlainText().strip()
        observacion = self.input_observacion.toPlainText().strip()

        # Validar campos obligatorios
        if not id_docente:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar un docente.")
            return
        if not fecha or not hora:
            QMessageBox.warning(self, "Advertencia", "La fecha y hora son obligatorias.")
            return

        # Preparar los datos para la inserción
        datos_tutoria = {
            "ID_Docente": id_docente,
            "Fecha_Tutoria": fecha,
            "Hora_Tutoria": hora,
            "Temario": temario,
            "Observacion": observacion,
        }

        try:
            # Registrar en la base de datos
            register_data("Tutoria", datos_tutoria)
            QMessageBox.information(self, "Éxito", "Tutoria registrada correctamente.")
            # Limpiar los campos
            self.combo_docente.setCurrentIndex(0)
            self.input_fecha.setDate(QDate.currentDate())
            self.input_hora.setTime(QTime.currentTime())
            self.input_temario.clear()
            self.input_observacion.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al registrar la tutoria: {e}")

#Ingresar Notas
class IngresarNotasWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ingresar Notas")
        self.setGeometry(100, 100, 500, 400)

        # Crear un QLabel para la imagen de fondo
        self.label_image = QLabel(self)
        self.label_image.setGeometry(0, 0, self.width(), self.height())

        # Construir la ruta relativa de la imagen
        image_path = os.path.join(os.path.dirname(os.getcwd()),"imagen3.jpg")
        if not os.path.exists(image_path):
            print(f"Error: La imagen no existe en la ruta: {image_path}")
        else:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print("Error: La imagen no se cargó correctamente.")
            else:
                # Ajustar la imagen al tamaño del QLabel manteniendo la proporción
                self.label_image.setPixmap(pixmap.scaled(
                    self.label_image.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))

        self.label_image.setAlignment(Qt.AlignCenter)
        self.label_image.lower()  # Asegurarse de que la imagen quede detrás de los widgets

        # Crear el layout principal
        layout = QVBoxLayout()

        # Selección de Estudiante
        self.label_estudiante = QLabel("Seleccione el Estudiante:")
        self.combo_estudiante = QComboBox()
        self.cargar_estudiantes()
        layout.addWidget(self.label_estudiante)
        layout.addWidget(self.combo_estudiante)

        # Selección de Tutoría
        self.label_tutoria = QLabel("Seleccione la Tutoria:")
        self.combo_tutoria = QComboBox()
        self.cargar_tutorias()
        layout.addWidget(self.label_tutoria)
        layout.addWidget(self.combo_tutoria)

        # Campo de Observaciones
        self.label_observaciones = QLabel("Observaciones:")
        self.input_observaciones = QTextEdit()
        layout.addWidget(self.label_observaciones)
        layout.addWidget(self.input_observaciones)

        # Campo de Calificación
        self.label_calificacion = QLabel("Calificación:")
        self.input_calificacion = QLineEdit()
        self.input_calificacion.setPlaceholderText("Ejemplo: 8.50")
        layout.addWidget(self.label_calificacion)
        layout.addWidget(self.input_calificacion)

        # Botón para guardar
        self.button_guardar = QPushButton("Registrar Nota")
        self.button_guardar.clicked.connect(self.guardar_nota)
        layout.addWidget(self.button_guardar)

        # Configurar el contenedor
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def cargar_estudiantes(self):
        """Carga los estudiantes desde la base de datos y los agrega al combo box."""
        try:
            resultados = query_data("Estudiante")
            for estudiante in resultados:
                id_estudiante = estudiante[0]  # Asumiendo que ID_Estudiante es la primera columna
                nombre_completo = f"{estudiante[1]} {estudiante[2]}"  # Nombre y Apellido
                self.combo_estudiante.addItem(nombre_completo, id_estudiante)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la lista de estudiantes: {e}")

    def cargar_tutorias(self):
        """Carga las tutorías desde la base de datos y las agrega al combo box."""
        try:
            resultados = query_data("Tutoria")
            for tutoria in resultados:
                id_tutoria = tutoria[0]  # Asumiendo que ID_Tutoria es la primera columna
                descripcion = f"{tutoria[2]} {tutoria[3]}"  # Fecha y Hora
                self.combo_tutoria.addItem(descripcion, id_tutoria)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la lista de tutorías: {e}")

    def guardar_nota(self):
        """Guarda los datos de la nota en la base de datos."""
        # Obtener datos del formulario
        id_estudiante = self.combo_estudiante.currentData()
        id_tutoria = self.combo_tutoria.currentData()
        observaciones = self.input_observaciones.toPlainText().strip()
        calificacion = self.input_calificacion.text().strip()

        # Validar campos obligatorios
        if not id_estudiante or not id_tutoria:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar un estudiante y una tutoría.")
            return
        if not calificacion or not calificacion.replace('.', '', 1).isdigit():
            QMessageBox.warning(self, "Advertencia", "La calificación debe ser un número válido.")
            return

        # Preparar los datos para la inserción
        datos_nota = {
            "ID_Estudiante": id_estudiante,
            "ID_Tutoria": id_tutoria,
            "Observaciones": observaciones,
            "Calificacion": float(calificacion),
        }

        try:
            # Registrar en la base de datos
            register_data("Detalles", datos_nota)
            QMessageBox.information(self, "Éxito", "Nota registrada correctamente.")
            # Limpiar los campos
            self.combo_estudiante.setCurrentIndex(0)
            self.combo_tutoria.setCurrentIndex(0)
            self.input_observaciones.clear()
            self.input_calificacion.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al registrar la nota: {e}")

#Consultar Tutoria
class ConsultarTutoriaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Consultar Tutoria")
        self.setGeometry(100, 100, 600, 400)

        # Layout principal
        layout = QVBoxLayout()

        # Crear el comboBox para seleccionar fecha
        self.combo_fecha = QComboBox()
        self.combo_fecha.currentIndexChanged.connect(self.consultar_tutoria)  # Conectar a la función que consulta las tutorías
        layout.addWidget(QLabel("Seleccione una fecha de Tutoria:"))
        layout.addWidget(self.combo_fecha)

        # Crear la tabla para mostrar los resultados
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)  # 5 columnas
        self.result_table.setHorizontalHeaderLabels(['ID Docente', 'Nombre Docente', 'Temario', 'Fecha Tutoria', 'Hora Tutoria'])
        layout.addWidget(self.result_table)

        # Botón de consulta
        self.button_consultar = QPushButton("Consultar")
        self.button_consultar.clicked.connect(self.consultar_tutoria)
        layout.addWidget(self.button_consultar)

        # Configurar el contenedor central
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Llamar a la función para cargar las fechas de las tutorías
        self.cargar_fechas()

    
    def cargar_fechas(self):
        query = "SELECT DISTINCT Fecha_Tutoria FROM Tutoria ORDER BY Fecha_Tutoria"

        try:
            # Ejecutar la consulta personalizada
            fechas = execute_query(query)  # Asegúrate de que esta función retorne resultados adecuados
            print(f"Resultados obtenidos: {fechas}")  # Depuración: verifica el formato

            if fechas:
                self.combo_fecha.clear()
                for fecha in fechas:
                    # Asumiendo que `fechas` es una lista de tuplas
                    fecha_str = str(fecha[0])  # Extrae el primer elemento de la tupla
                    print(f"Fecha obtenida: {fecha_str}")
                    self.combo_fecha.addItem(fecha_str)
            else:
                QMessageBox.warning(self, "No hay fechas", "No se han encontrado fechas de tutorías.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar las fechas: {e}")

    def consultar_tutoria(self):
        fecha_seleccionada = self.combo_fecha.currentText().strip()

        if not fecha_seleccionada:
            QMessageBox.warning(self, "Advertencia", "Seleccione una fecha.")
            return

        # Consulta SQL para obtener los datos de la tutoria según la fecha seleccionada
        query = """
        SELECT 
            d.ID_Docente, 
            d.Nombre_Docente, 
            t.Temario, 
            t.Fecha_Tutoria, 
            t.Hora_Tutoria
        FROM 
            Tutoria t
        INNER JOIN 
            Docente d ON t.ID_Docente = d.ID_Docente
        WHERE 
            t.Fecha_Tutoria = %s
        """

        try:
            # Ejecutar la consulta con la fecha seleccionada
            tutoria_data = execute_query(query, (fecha_seleccionada,))

            if tutoria_data:
                self.result_table.setRowCount(0)  # Limpiar la tabla
                for row_number, row_data in enumerate(tutoria_data):
                    # Insertar una nueva fila en la tabla
                    self.result_table.insertRow(row_number)

                    # Manejar valores nulos o vacíos en las celdas
                    id_docente = str(row_data[0])  # Índice 0: ID_Docente
                    nombre_docente = row_data[1] or "Sin nombre"  # Índice 1: Nombre_Docente
                    temario = row_data[2] or "Sin temario"  # Índice 2: Temario
                    fecha_tutoria = str(row_data[3])  # Índice 3: Fecha_Tutoria
                    hora_tutoria = str(row_data[4])  # Índice 4: Hora_Tutoria

                    # Llenar las celdas con los datos
                    self.result_table.setItem(row_number, 0, QTableWidgetItem(id_docente))
                    self.result_table.setItem(row_number, 1, QTableWidgetItem(nombre_docente))
                    self.result_table.setItem(row_number, 2, QTableWidgetItem(temario))
                    self.result_table.setItem(row_number, 3, QTableWidgetItem(fecha_tutoria))
                    self.result_table.setItem(row_number, 4, QTableWidgetItem(hora_tutoria))
            else:
                QMessageBox.information(self, "No hay tutorías", "No se encontraron tutorías para la fecha seleccionada.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al consultar las tutorías: {e}")

#Consultar Notas
class ConsultarNotasWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Consultar Notas")
        self.setGeometry(100, 100, 600, 400)

        # Crear el layout principal
        layout = QVBoxLayout()

        # Campo para ingresar el ID del estudiante
        self.label_id_estudiante = QLabel("Ingrese el ID del Estudiante:")
        self.input_id_estudiante = QLineEdit()
        self.input_id_estudiante.setPlaceholderText("Ejemplo: 1")
        layout.addWidget(self.label_id_estudiante)
        layout.addWidget(self.input_id_estudiante)

        # Botón para consultar
        self.button_consultar = QPushButton("Consultar Notas")
        self.button_consultar.clicked.connect(self.consultar_notas)
        layout.addWidget(self.button_consultar)

        # Tabla para mostrar los resultados
        self.result_table = QtWidgets.QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["ID Estudiante", "Nombre", "Temario", "Calificación"])
        layout.addWidget(self.result_table)

        # Configurar el contenedor
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def consultar_notas(self):
        id_estudiante = self.input_id_estudiante.text().strip()

        if not id_estudiante:
            QMessageBox.warning(self, "Advertencia", "El campo 'ID Estudiante' es obligatorio.")
            return

        query = """
            SELECT
                e.ID_Estudiante,
                e.Nombre_Estudiante,
                t.Temario,
                d.Calificacion
            FROM
                Estudiante e
            INNER JOIN
                Detalles d ON e.ID_Estudiante = d.ID_Estudiante
            INNER JOIN
                Tutoria t ON d.ID_Tutoria = t.ID_Tutoria
            WHERE
                e.ID_Estudiante = %s
        """
        #   
        def query_data2(query, params=None):
                conn = connect_to_db()
                if conn:
                    try:
                        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                            cursor.execute(query, params if params else ())
                            results = cursor.fetchall()
                            return results
                    except Exception as e:
                        print(f"Error al consultar datos de la tabla {query}: {e}")
                        return []
                    finally:
                        conn.close()
        #  
        try:
            # Asegúrate de pasar los parámetros como una tupla
            resultados = query_data2(query, (id_estudiante,))
            
            if resultados:
                self.result_table.setRowCount(0)  # Limpiar la tabla
                for row_number, row_data in enumerate(resultados):
                    # Crear una nueva fila en la tabla
                    self.result_table.insertRow(row_number)
                    
                    # Insertar los datos en las columnas correspondientes
                    self.result_table.setItem(row_number, 0, QTableWidgetItem(str(row_data['id_estudiante'])))
                    self.result_table.setItem(row_number, 1, QTableWidgetItem(row_data['nombre_estudiante']))
                    self.result_table.setItem(row_number, 2, QTableWidgetItem(row_data['temario'] if row_data['temario'] else 'Sin temario'))
                    self.result_table.setItem(row_number, 3, QTableWidgetItem(str(row_data['calificacion'])))
            else:
                QMessageBox.information(self, "Sin Resultados", "No se encontraron notas para el ID proporcionado.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al consultar las notas: {e}")

#Reporte General
class GenerarReporteGeneralWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generar Reporte General")
        self.setGeometry(100, 100, 600, 400)

        # Layout principal
        layout = QVBoxLayout()

        # Campos para ingresar el ID del estudiante
        self.label_id_estudiante = QLabel("ID Estudiante:")
        self.input_id_estudiante = QLineEdit()
        layout.addWidget(self.label_id_estudiante)
        layout.addWidget(self.input_id_estudiante)

        # Botón para generar el reporte
        self.button_generar_reporte = QPushButton("Generar Reporte")
        self.button_generar_reporte.clicked.connect(self.generar_reporte)
        layout.addWidget(self.button_generar_reporte)

        # Tabla para mostrar los resultados
        self.table = QTableWidget()
        layout.addWidget(self.table)

        # Botón para generar PDF
        self.button_generar_pdf = QPushButton("Generar PDF")
        self.button_generar_pdf.clicked.connect(self.generar_pdf)
        layout.addWidget(self.button_generar_pdf)

        # Configurar el contenedor principal
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def generar_reporte(self):
        # Obtener el ID del estudiante desde el input
        id_estudiante = self.input_id_estudiante.text().strip()

        # Validar que el ID del estudiante no esté vacío
        if not id_estudiante:
            QMessageBox.warning(self, "Advertencia", "Por favor ingrese un ID de estudiante.")
            return

        # Crear la consulta para obtener los datos del estudiante, temario y calificación
        query = """
            SELECT
                e.ID_Estudiante,
                e.Nombre_Estudiante,
                t.Temario,
                d.Calificacion
            FROM
                Estudiante e
            INNER JOIN
                Detalles d ON e.ID_Estudiante = d.ID_Estudiante
            INNER JOIN
                Tutoria t ON d.ID_Tutoria = t.ID_Tutoria
            WHERE
                e.ID_Estudiante = %s
        """
        params = (id_estudiante,)

        # Ejecutar la consulta usando la función query_with_joins
        resultados = query_with_joins(query, params)

        # Verificar si hay resultados
        if not resultados:
            QMessageBox.warning(self, "No se encontraron resultados", "No se encontraron resultados para este ID de estudiante.")
            return

        # Limpiar la tabla antes de mostrar nuevos resultados
        self.table.setRowCount(0)
        self.table.setColumnCount(4)  # Número de columnas: ID, Nombre, Temario, Calificación
        self.table.setHorizontalHeaderLabels(["ID Estudiante", "Nombre Estudiante", "Temario", "Calificación"])

        # Llenar la tabla con los resultados
        for row_index, resultado in enumerate(resultados):
            self.table.insertRow(row_index)
            self.table.setItem(row_index, 0, QTableWidgetItem(str(resultado["id_estudiante"])))
            self.table.setItem(row_index, 1, QTableWidgetItem(resultado["nombre_estudiante"]))
            self.table.setItem(row_index, 2, QTableWidgetItem(resultado["temario"] if resultado["temario"] else "N/A"))
            self.table.setItem(row_index, 3, QTableWidgetItem(str(resultado["calificacion"])))

    def generar_pdf(self):
        # Obtener el ID del estudiante desde el input
        id_estudiante = self.input_id_estudiante.text().strip()

        # Validar que el ID no esté vacío
        if not id_estudiante:
            QMessageBox.warning(self, "Advertencia", "Por favor ingrese un ID de estudiante.")
            return

        # Crear la consulta para obtener los datos del estudiante, temario y calificación
        query = """
            SELECT
                e.ID_Estudiante,
                e.Nombre_Estudiante,
                t.Temario,
                d.Calificacion
            FROM
                Estudiante e
            INNER JOIN
                Detalles d ON e.ID_Estudiante = d.ID_Estudiante
            INNER JOIN
                Tutoria t ON d.ID_Tutoria = t.ID_Tutoria
            WHERE
                e.ID_Estudiante = %s
        """
        params = (id_estudiante,)

        # Ejecutar la consulta usando la función query_with_joins
        resultados = query_with_joins(query, params)

        # Verificar si no se encontraron resultados
        if not resultados:
            QMessageBox.warning(self, "No encontrado", "No se encontraron datos para generar el PDF.")
            return

        # Dialogo para seleccionar ubicación del archivo
        archivo, _ = QFileDialog.getSaveFileName(self, "Guardar como", "", "PDF files (*.pdf);;All files (*)")
        if not archivo:
            return

        # Crear documento PDF
        pdf = SimpleDocTemplate(archivo, pagesize=letter)

        # Encabezado de la tabla
        datos = [["ID Estudiante", "Nombre Estudiante", "Temario", "Calificación"]]

        # Agregar filas de datos
        for row in resultados:
            datos.append([
                row['id_estudiante'],
                row['nombre_estudiante'],
                row['temario'] if row['temario'] else "N/A",  # Si no hay temario, poner "N/A"
                row['calificacion']
            ])

        # Establecer el estilo de la tabla
        tabla = Table(datos)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Fondo gris para el encabezado
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Texto blanco en el encabezado
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Alineación centrada
            ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Borde de la tabla
            ('FONTSIZE', (0, 0), (-1, -1), 10),  # Tamaño de fuente de la tabla
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Espacio en la parte inferior del encabezado
            ('TOPPADDING', (0, 0), (-1, -1), 10),  # Espacio superior en la tabla
        ]))

        # Generar el PDF
        pdf.build([tabla])

        # Mostrar mensaje de éxito
        QMessageBox.information(self, "Éxito", f"Reporte generado y guardado en: {archivo}")

#Reporte Detalle                                                         
class GenerarReporteDetalleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generar Reporte Detalle")
        self.setGeometry(100, 100, 600, 400)

        # Layout principal
        layout = QVBoxLayout()

        # Etiqueta y campo de texto para ingresar el id_tutoria
        self.label_id_tutoria = QLabel("Ingresar ID Tutoria:")
        self.input_id_tutoria = QLineEdit()
        layout.addWidget(self.label_id_tutoria)
        layout.addWidget(self.input_id_tutoria)

        # Botón para generar el reporte
        self.button_generar_reporte = QPushButton("Generar Reporte")
        self.button_generar_reporte.clicked.connect(self.generar_reporte)
        layout.addWidget(self.button_generar_reporte)

        # Tabla para mostrar los resultados
        self.table = QTableWidget()
        layout.addWidget(self.table)

        # Botón para generar el PDF
        self.button_generar_pdf = QPushButton("Generar PDF")
        self.button_generar_pdf.clicked.connect(self.generar_pdf)
        layout.addWidget(self.button_generar_pdf)

        # Configurar el contenedor principal
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Inicializar un atributo para guardar los resultados
        self.results = []

    def generar_reporte(self):
        # Obtener el ID de la tutoria desde el QLineEdit
        id_tutoria = self.input_id_tutoria.text().strip()

        # Verificar que el ID de tutoria no esté vacío
        if not id_tutoria:
            QMessageBox.warning(self, "Advertencia", "Por favor ingrese un ID de Tutoria.")
            return

        # Crear la consulta para obtener los detalles de la tutoria seleccionada
        query = """
            SELECT
                t.ID_Tutoria,
                t.Fecha_Tutoria,
                t.Hora_Tutoria,
                t.Temario,
                e.Nombre_Estudiante,
                d.Calificacion
            FROM
                Tutoria t
            INNER JOIN
                Detalles d ON t.ID_Tutoria = d.ID_Tutoria
            INNER JOIN
                Estudiante e ON d.ID_Estudiante = e.ID_Estudiante
            WHERE
                t.ID_Tutoria = %s
        """
        params = (id_tutoria,)

        # Ejecutar la consulta usando la función query_with_joins
        resultados = query_with_joins(query, params)

        # Verificar si no se encontraron resultados
        if not resultados:
            QMessageBox.warning(self, "No encontrado", "No se encontraron datos para esta tutoria.")
            return

        # Guardar los resultados en el atributo 'self.results'
        self.results = resultados

        # Limpiar la tabla antes de mostrar nuevos resultados
        self.table.setRowCount(0)
        self.table.setColumnCount(6)  # Número de columnas: ID, Fecha, Hora, Temario, Estudiante, Calificación
        self.table.setHorizontalHeaderLabels(["ID Tutoria", "Fecha", "Hora", "Temario", "Nombre Estudiante", "Calificación"])

        # Llenar la tabla con los resultados
        for row_index, resultado in enumerate(resultados):
            self.table.insertRow(row_index)
            self.table.setItem(row_index, 0, QTableWidgetItem(str(resultado["id_tutoria"])))
            self.table.setItem(row_index, 1, QTableWidgetItem(str(resultado["fecha_tutoria"])))
            self.table.setItem(row_index, 2, QTableWidgetItem(str(resultado["hora_tutoria"])))
            self.table.setItem(row_index, 3, QTableWidgetItem(resultado["temario"] if resultado["temario"] else "N/A"))
            self.table.setItem(row_index, 4, QTableWidgetItem(resultado["nombre_estudiante"]))
            self.table.setItem(row_index, 5, QTableWidgetItem(str(resultado["calificacion"])))

    def generar_pdf(self):
        # Verificar si hay resultados disponibles
        if not self.results:
            QMessageBox.warning(self, "Error", "No hay datos para generar el PDF. Realice una consulta primero.")
            return

        # Dialogo para seleccionar ubicación del archivo
        archivo, _ = QFileDialog.getSaveFileName(self, "Guardar como", "", "PDF files (*.pdf);;All files (*)")
        if not archivo:
            return

        # Crear documento PDF
        pdf = SimpleDocTemplate(archivo, pagesize=letter)

        # Encabezado de la tabla
        datos = [["ID Tutoria", "Fecha", "Hora", "Temario", "Nombre Estudiante", "Calificación"]]

        # Agregar filas de datos
        for row in self.results:
            datos.append([
                row['id_tutoria'],
                row['fecha_tutoria'],
                row['hora_tutoria'],
                row['temario'] if row['temario'] else "N/A",
                row['nombre_estudiante'],
                row['calificacion']
            ])

        # Establecer el estilo de la tabla
        tabla = Table(datos)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Fondo gris para el encabezado
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Texto blanco en el encabezado
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Alineación centrada
            ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Borde de la tabla
            ('FONTSIZE', (0, 0), (-1, -1), 10),  # Tamaño de fuente de la tabla
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Espacio en la parte inferior del encabezado
            ('TOPPADDING', (0, 0), (-1, -1), 10),  # Espacio superior en la tabla
        ]))

        # Generar el PDF
        pdf.build([tabla])

        # Mostrar mensaje de éxito
        QMessageBox.information(self, "Éxito", f"Reporte generado y guardado en: {archivo}")

#Menubar Principal           
class Menubar(QtWidgets.QMainWindow):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.setupUi(self)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("Asistencias")
        MainWindow.setWindowTitle("Asistencias")
        MainWindow.resize(800, 600)
        MainWindow.setStyleSheet("background-color: #53C8DB;")

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)
        
        # Crear un QLabel para mostrar la imagen de fondo
        self.label_image = QtWidgets.QLabel(self.centralwidget)
        self.label_image.setGeometry(0, 0, MainWindow.width(), MainWindow.height())

        # Construir la ruta de la imagen
        image_path = os.path.join(os.path.dirname(os.getcwd()),"SistemaGeneral.png")
        if not os.path.exists(image_path):
            print(f"Error: La imagen no existe en la ruta: {image_path}")
        else:
            pixmap = QtGui.QPixmap(image_path)
            if pixmap.isNull():
                print("Error: La imagen no se cargó correctamente.")
            else:
                # Ajustar la imagen al tamaño del QLabel
                self.label_image.setPixmap(pixmap.scaled(
                    self.label_image.size(),
                    QtCore.Qt.KeepAspectRatioByExpanding,
                    QtCore.Qt.SmoothTransformation
                ))
        
        self.label_image.setAlignment(QtCore.Qt.AlignCenter)
        self.label_image.lower()

        # Menubar
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setStyleSheet("background-color: white;")

        # Menús principales
        self.menuRegistrar = QtWidgets.QMenu("Registrar", self.menubar)
        self.menuIngresar = QtWidgets.QMenu("Ingresar", self.menubar)
        self.menuConsultar = QtWidgets.QMenu("Consultar", self.menubar)
        self.menuReporte = QtWidgets.QMenu("Reporte", self.menubar)
        self.menuSesion = QtWidgets.QMenu("Sesión", self.menubar)

        # Submenús para "Registrar"
        self.actionRegistrarDocente = QtWidgets.QAction("Registrar Docente", self)
        self.actionRegistrarEstudiante = QtWidgets.QAction("Registrar Estudiante", self)
        self.actionRegistrarTutor = QtWidgets.QAction("Registrar Tutor", self)
        self.actionRegistrarAsignatura = QtWidgets.QAction("Registrar Asignatura", self)

        # Submenús para "Ingresar"
        self.actionIngresarTutoria = QtWidgets.QAction("Ingresar Tutoria", self)
        self.actionIngresarNotas = QtWidgets.QAction("Ingresar Notas", self)

        # Submenús para "Consultar"
        self.actionConsultarTutoria = QtWidgets.QAction("Consultar Tutoria", self)
        self.actionConsultarNotas = QtWidgets.QAction("Consultar Notas", self)

        # Submenús para "Reporte"
        self.actionGenerarReporteGeneral = QtWidgets.QAction("Generar Reporte General", self)
        self.actionGenerarReporteDetalle = QtWidgets.QAction("Generar Reporte Detalle", self)

        # Submenú para "Sesión"
        self.actionAdministrarUsuarios = QtWidgets.QAction("Administrar Usuarios", self)

        # Agrega las acciones al menú Registrar
        self.menuRegistrar.addAction(self.actionRegistrarDocente)
        self.menuRegistrar.addAction(self.actionRegistrarEstudiante)
        self.menuRegistrar.addAction(self.actionRegistrarTutor)
        self.menuRegistrar.addAction(self.actionRegistrarAsignatura)

        # Agregar las acciones al menú Ingresar
        self.menuIngresar.addAction(self.actionIngresarTutoria)
        self.menuIngresar.addAction(self.actionIngresarNotas)

        # Agregar las acciones al menú Consultar
        self.menuConsultar.addAction(self.actionConsultarTutoria)
        self.menuConsultar.addAction(self.actionConsultarNotas)

        # Agregar las acciones al menú Reporte
        self.menuReporte.addAction(self.actionGenerarReporteGeneral)
        self.menuReporte.addAction(self.actionGenerarReporteDetalle)

        # Conectar acciones a métodos

        #registrar
        self.actionRegistrarDocente.triggered.connect(self.abrir_registrar_docente)
        self.actionRegistrarEstudiante.triggered.connect(self.abrir_registrar_estudiante)
        self.actionRegistrarTutor.triggered.connect(self.abrir_registrar_tutor)
        self.actionRegistrarAsignatura.triggered.connect(self.abrir_registrar_asignatura) 
        #ingresar
        self.actionIngresarTutoria.triggered.connect(self.abrir_ingresar_tutoria)
        self.actionIngresarNotas.triggered.connect(self.abrir_ingresar_notas)
        #consultar
        self.actionConsultarTutoria.triggered.connect(self.abrir_consultar_tutoria)
        self.actionConsultarNotas.triggered.connect(self.abrir_consultar_notas)
        #reportes
        self.actionGenerarReporteGeneral.triggered.connect(self.abrir_generar_reporte_general)
        self.actionGenerarReporteDetalle.triggered.connect(self.abrir_generar_reporte_detalle)

        # Agregar acción "Cerrar sesión" al menú Sesión
        self.actionCerrarSesion = QtWidgets.QAction("Cerrar sesión", self)
        self.actionCerrarSesion.triggered.connect(self.cerrar_sesion)  # Conecta al método
        self.menuSesion.addAction(self.actionCerrarSesion)

        #accion Administrar Sesion
        self.menuSesion.addAction(self.actionAdministrarUsuarios)
        #abrir ventana
        self.actionAdministrarUsuarios.triggered.connect(self.abrir_administrar_usuarios)

        # Agregar los menús a la barra de menú
        self.menubar.addMenu(self.menuRegistrar)
        self.menubar.addMenu(self.menuIngresar)
        self.menubar.addMenu(self.menuConsultar)
        self.menubar.addMenu(self.menuReporte)
        self.menubar.addMenu(self.menuSesion)

        def resizeEvent(self, event):
            # Reajustar la imagen de fondo al redimensionar la ventana
            if not self.label_image.pixmap().isNull():
                self.label_image.setPixmap(self.label_image.pixmap().scaled(
                    self.label_image.size(),
                    QtCore.Qt.KeepAspectRatioByExpanding,
                    QtCore.Qt.SmoothTransformation
                ))
            super().resizeEvent(event)
        MainWindow.setMenuBar(self.menubar)

        self.configure_menubar()

    #Manejo de roles
    def configure_menubar(self):
        """Configura la barra de menús según el rol del usuario."""
        if self.user_role != "admin":
            self.actionAdministrarUsuarios.setDisabled(True)
            
        # Deshabilitar menús que no están permitidos para el rol actual
        if self.user_role == "estudiante":
            # Rol estudiante
            self.menuRegistrar.setDisabled(False)  # El estudiante puede registrarse a sí mismo
            self.menuReporte.setDisabled(True)    # El estudiante no puede generar reportes
            self.menuConsultar.setDisabled(False) # El estudiante puede consultar material de estudio

            # Habilitar solo las opciones permitidas para el estudiante
            self.actionRegistrarEstudiante.setDisabled(False)  # El estudiante puede registrarse a sí mismo

            # El estudiante puede ingresar material de estudio
            self.actionIngresarTutoria.setDisabled(False)
            
            # El estudiante puede consultar material de estudio
            self.actionConsultarTutoria.setDisabled(False)

            # Deshabilitar las demás opciones que no son permitidas para el estudiante
            self.actionRegistrarDocente.setDisabled(True)
            self.actionRegistrarTutor.setDisabled(True)
            self.actionRegistrarAsignatura.setDisabled(True)
            self.actionIngresarNotas.setDisabled(True)
            self.actionConsultarNotas.setDisabled(True)
            self.actionGenerarReporteGeneral.setDisabled(True)
            self.actionGenerarReporteDetalle.setDisabled(True)

        elif self.user_role == "tutor":
            # Rol tutor
            self.menuRegistrar.setDisabled(False)  # Los tutores pueden registrarse a sí mismos
            self.menuReporte.setDisabled(True)     # Los tutores no pueden generar reportes
            self.menuConsultar.setDisabled(False)  # Los tutores pueden consultar material y notas

            # Habilitar solo las opciones permitidas para el tutor
            self.actionRegistrarTutor.setDisabled(False)  # Los tutores pueden registrarse a sí mismos
            self.actionIngresarTutoria.setDisabled(False) # Los tutores pueden ingresar material de estudio
            self.actionConsultarTutoria.setDisabled(False) # Los tutores pueden consultar material de estudio
            self.actionConsultarNotas.setDisabled(False)   # Los tutores pueden consultar notas

            # Deshabilitar las demás opciones que no son permitidas para el tutor
            self.actionRegistrarDocente.setDisabled(True)
            self.actionRegistrarEstudiante.setDisabled(True)
            self.actionRegistrarAsignatura.setDisabled(True)
            self.actionIngresarNotas.setDisabled(True)  # Los tutores no pueden ingresar notas
            self.actionGenerarReporteGeneral.setDisabled(True)
            self.actionGenerarReporteDetalle.setDisabled(True)

        elif self.user_role == "docente":
            # Rol docente
            self.menuRegistrar.setDisabled(False)  # Los docentes pueden registrarse a sí mismos
            self.menuReporte.setDisabled(False)    # Los docentes pueden generar reportes
            self.menuConsultar.setDisabled(False)  # Los docentes pueden consultar material y notas

            # Habilitar todas las opciones permitidas para el docente
            self.actionRegistrarDocente.setDisabled(False)  # Los docentes pueden registrarse a sí mismos
            self.actionIngresarTutoria.setDisabled(False)  # Los docentes pueden ingresar material de estudio
            self.actionIngresarNotas.setDisabled(False)    # Los docentes pueden ingresar notas
            self.actionConsultarNotas.setDisabled(False)   # Los docentes pueden consultar notas
            self.actionGenerarReporteGeneral.setDisabled(False)  # Los docentes pueden generar reportes generales
            self.actionGenerarReporteDetalle.setDisabled(False)  # Los docentes pueden generar reportes detallados

            # Deshabilitar las demás opciones que no son permitidas para el docente
            self.actionRegistrarEstudiante.setDisabled(True)
            self.actionRegistrarTutor.setDisabled(True)
            self.actionRegistrarAsignatura.setDisabled(True)
        
        else:
            # Para cualquier otro rol (si es que existe)
            self.menuRegistrar.setDisabled(False)
            self.menuReporte.setDisabled(False)
            self.menuConsultar.setDisabled(False)
            self.menuSesion.setDisabled(False)


    def cerrar_sesion(self):
        """Cierra la sesión y regresa a la ventana de inicio de sesión."""
        from app import LoginWindow  # Importar la ventana de Login (o ajusta el import según tu estructura)
        
        self.login_window = LoginWindow() 
        self.login_window.show() 
        self.close() 

    def abrir_registrar_docente(self):
        self.registrar_docente_window = RegistrarDocenteWindow()
        self.registrar_docente_window.show()

    def abrir_registrar_estudiante(self):
        self.registrar_estudiante_window = RegistrarEstudianteWindow()
        self.registrar_estudiante_window.show()    

    def abrir_registrar_tutor(self):
        self.registrar_tutor_window = RegistrarTutorWindow()
        self.registrar_tutor_window.show()
    
    def abrir_registrar_asignatura(self):
        self.registrar_asignatura_window = RegistrarAsignaturaWindow()
        self.registrar_asignatura_window.show()
    
    def abrir_ingresar_tutoria(self):
        self.ingresar_tutoria_window = IngresarTutoriaWindow()
        self.ingresar_tutoria_window.show()

    def abrir_ingresar_notas(self):
        self.ingresar_notas_window = IngresarNotasWindow()
        self.ingresar_notas_window.show()  

    def abrir_consultar_tutoria(self):
        self.window = ConsultarTutoriaWindow()
        self.window.show()
        
    def abrir_consultar_notas(self):
        self.consultar_notas_window = ConsultarNotasWindow()
        self.consultar_notas_window.show()

    def abrir_generar_reporte_general(self):
        self.reporte_general_window = GenerarReporteGeneralWindow()
        self.reporte_general_window.show()

    def abrir_generar_reporte_detalle(self):
        self.generar_reporte_detalle_window = GenerarReporteDetalleWindow()
        self.generar_reporte_detalle_window.show()

    def abrir_administrar_usuarios(self):
        self.admin_window = AdminUsuariosWindow()
        self.admin_window.show()    