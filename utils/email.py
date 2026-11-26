"""Envío de correos por Gmail (SMTP con SSL, puerto 465).

Las credenciales se leen de .env (CORREO_REMITENTE y CORREO_CLAVE_APP).
Si no están configuradas, no se envía nada y se avisa por consola.
"""
import os
import smtplib
from email.message import EmailMessage


def enviar_correo_bienvenida(destinatario, nombre, usuario, contrasena_provisional):
    remitente = os.environ.get("CORREO_REMITENTE", "")
    clave = os.environ.get("CORREO_CLAVE_APP", "")
    if not remitente or not clave:
        raise RuntimeError("Falta CORREO_REMITENTE o CORREO_CLAVE_APP en .env")

    msg = EmailMessage()
    msg["Subject"] = "Bienvenido al sistema"
    msg["From"] = remitente
    msg["To"] = destinatario
    msg.set_content(
        f"Hola {nombre},\n\n"
        "Se creó tu cuenta en el sistema.\n"
        f"Usuario: {usuario}\n"
        f"Contraseña provisional: {contrasena_provisional}\n\n"
        "Podrás iniciar sesión cuando un administrador active tu cuenta. "
        "En tu primer acceso se te pedirá cambiar la contraseña."
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as smtp:
        smtp.login(remitente, clave)
        smtp.send_message(msg)