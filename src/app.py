from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QWidget, QMessageBox, QComboBox
)
from PyQt5.QtGui import QPixmap
from PyQt5 import QtCore
from menubar import Menubar  # Importa Menubar
from conexion import register_data, get_user_role  # Funciones modularizadas
import os

# Ventana de Registro
class RegisterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro de Usuarios")
        self.setGeometry(100, 100, 300, 300)

        layout = QVBoxLayout()

        # Imagen superior
        self.label_image = QLabel()
        image_path = os.path.join(os.path.dirname(os.getcwd()),"uleam.jpeg")
        if not os.path.exists(image_path):
            print(f"Error: La imagen no existe en la ruta: {image_path}")
        else:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print("Error: La imagen no se cargó correctamente.")
            else:
                self.label_image.setPixmap(pixmap.scaled(100, 100))
        self.label_image.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.label_image)

        self.label_username = QLabel("Nombre de Usuario:")
        self.input_username = QLineEdit()
        layout.addWidget(self.label_username)
        layout.addWidget(self.input_username)

        self.label_password = QLabel("Contraseña:")
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.label_password)
        layout.addWidget(self.input_password)

        self.label_role = QLabel("Rol:")
        self.combo_role = QComboBox()
        self.combo_role.addItems(["docente", "tutor", "estudiante"])
        layout.addWidget(self.label_role)
        layout.addWidget(self.combo_role)

        self.button_register = QPushButton("Registrar")
        self.button_register.clicked.connect(self.register_data)
        layout.addWidget(self.button_register)

        self.button_to_login = QPushButton("Ir a Login")
        self.button_to_login.clicked.connect(self.go_to_login)
        layout.addWidget(self.button_to_login)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def register_data(self):
        username = self.input_username.text()
        password = self.input_password.text()
        rol = self.combo_role.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Advertencia", "Todos los campos son obligatorios.")
            return

        data = {'nombre_usuario': username, 'clave': password, 'rol': rol}
        register_data('usuario', data)

        QMessageBox.information(self, "Éxito", "Usuario registrado correctamente.")
        self.input_username.clear()
        self.input_password.clear()

    def go_to_login(self):
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

# Ventana de Login
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ingreso")
        self.setGeometry(100, 100, 300, 300)

        layout = QVBoxLayout()

        # Imagen superior
        self.label_image = QLabel()
        image_path = os.path.join(os.path.dirname(os.getcwd()),"uleam.jpeg")
        if not os.path.exists(image_path):
            print(f"Error: La imagen no existe en la ruta: {image_path}")
        else:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print("Error: La imagen no se cargó correctamente.")
            else:
                self.label_image.setPixmap(pixmap.scaled(100, 100))
        self.label_image.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.label_image)
        

        self.label_username = QLabel("Nombre de Usuario:")
        self.input_username = QLineEdit()
        layout.addWidget(self.label_username)
        layout.addWidget(self.input_username)

        self.label_password = QLabel("Contraseña:")
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.label_password)
        layout.addWidget(self.input_password)

        self.button_login = QPushButton("Iniciar Sesión")
        self.button_login.clicked.connect(self.login_user)
        layout.addWidget(self.button_login)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def login_user(self):
        username = self.input_username.text()
        password = self.input_password.text()

        if not username or not password:
            QMessageBox.warning(self, "Advertencia", "Todos los campos son obligatorios.")
            return

        rol = get_user_role(username, password)
        if rol:
            QMessageBox.information(self, "Éxito", f"Bienvenido, {username}. Rol: {rol}")

            self.main_window = Menubar(rol)  # Pasa el rol a Menubar
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Error", "Credenciales incorrectas.")

# Main
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    # Verifica si el usuario ya ha registrado (ejemplo con archivo config.txt)
    if os.path.exists("config.txt") and "user_registered" in open("config.txt").read():
        login_window = LoginWindow()
        login_window.show()
    else:
        register_window = RegisterWindow()
        register_window.show()

    sys.exit(app.exec_())
