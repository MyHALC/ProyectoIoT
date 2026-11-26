from .usuarios_controller import UsuariosController


class AdministradoresController(UsuariosController):
    tipo = 'administrador'
