import os
import mysql.connector
from email import policy
from email.parser import BytesParser
from datetime import datetime

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="correos",
        password="correo_0110",
        database="correos",
        connection_timeout=300  # Tiempo de espera de 300 segundos
    )

def save_email(db_connection, sender, recipient, cc, subject, body, date, category_color, attachments):
    cursor = db_connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO emails (sender, recipient, cc, subject, body, date, category_color, attachments) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (sender, recipient, cc, subject, body, date, category_color, attachments)
        )
        db_connection.commit()
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_DUP_ENTRY:
            print(f"Email ya existente: {sender} - {subject} en {date}")
        else:
            print(f"Error: {err}")
    finally:
        cursor.close()

def extract_attachments(msg):
    attachments = []
    for part in msg.iter_attachments():
        if part.get_content_disposition() == 'attachment':
            file_data = part.get_payload(decode=True)
            attachments.append(file_data)  # Guarda solo el contenido del adjunto
    return attachments

def process_eml_file(file_path, db_connection):
    with open(file_path, 'rb') as file:
        msg = BytesParser(policy=policy.default).parse(file)

    sender = msg['From']
    recipient = msg['To']
    cc = msg.get('Cc', '')
    subject = msg['Subject']
    body = msg.get_body(preferencelist=('plain')).get_content()
    date = msg['Date']
    category_color = msg.get('X-Category-Color', '')

    if date:
        date = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %z").astimezone()

    attachments = extract_attachments(msg)
    attachments_data = None

    if attachments:
        # Convertir los adjuntos a un formato BLOB
        attachments_data = b''.join(attachments)  # Almacena todos los adjuntos como un solo BLOB

    save_email(db_connection, sender, recipient, cc, subject, body, date, category_color, attachments_data)

def main(directory):
    db_connection = connect_db()
    for filename in os.listdir(directory):
        if filename.endswith('.eml'):
            file_path = os.path.join(directory, filename)
            print(f"Procesando: {file_path}")
            process_eml_file(file_path, db_connection)
            # Eliminar el archivo después de procesarlo
            os.remove(file_path)
            print(f"Archivo eliminado: {file_path}")
    db_connection.close()

if __name__ == "__main__":
    directory = "C:/correos"
    main(directory)
