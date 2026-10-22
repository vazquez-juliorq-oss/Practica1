"""
Pipeline de ingesta de datos y perfilamiento en AWS S3.

Este script realiza la ingesta de archivos estructurados (CSV) y 
semiestructurados (JSON) en un bucket de Amazon S3. Posteriormente,
descarga los objetos directamente a memoria RAM (sin escribir en disco)
para realizar un perfilamiento de datos y análisis estadístico.
"""

import io
import json
import os
import boto3
import pandas as pd

# -----------------------------------------------------------------------------
# CONFIGURACIÓN Y PARÁMETROS DE AWS S3
# -----------------------------------------------------------------------------
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "TU_AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv(
    "AWS_SECRET_ACCESS_KEY", "TU_AWS_SECRET_ACCESS_KEY"
)
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN", "TU_AWS_SESSION_TOKEN")

BUCKET_NAME = os.getenv("BUCKET_NAME", "nombre-de-tu-bucket")

# Inicialización del cliente S3 mediante Boto3
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
)


def generar_y_subir_archivos_prueba():
    """Genera datos de prueba (CSV y JSON) y los sube al bucket S3."""
    print("=" * 70)
    print("=== PASO 1: GENERACIÓN Y SUBIDA DE ARCHIVOS A S3 ===")
    print("=" * 70)

    # 1. Dataset estructurado: CSV
    csv_content = (
        "id_transaccion,monto,fecha_transaccion,tipo_pago\n"
        "1001,150.50,2026-10-18,Tarjeta\n"
        "1002,89.00,2026-10-18,Efectivo\n"
        "1003,1200.00,2026-10-17,Transferencia\n"
        "1004,45.25,2026-10-16,Tarjeta\n"
        "1005,310.00,2026-10-15,Efectivo\n"
    )

    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key="raw/transacciones.csv",
        Body=csv_content.encode("utf-8"),
    )
    print(" -> Archivo 'raw/transacciones.csv' subido correctamente a S3.")

    # 2. Dataset semiestructurado: JSON
    json_data = [
        {
            "device_id": "sensor_01",
            "timestamp": "2026-10-18T10:00:00Z",
            "status": "OK",
            "payload": {"temperature": 23.5, "humidity": 60.2},
        },
        {
            "device_id": "sensor_02",
            "timestamp": "2026-10-18T10:01:00Z",
            "status": "WARNING",
            "payload": {"temperature": 38.1, "humidity": 75.0},
        },
        {
            "device_id": "sensor_03",
            "timestamp": "2026-10-18T10:02:00Z",
            "status": "CRITICAL",
            "payload": {"temperature": 52.4, "humidity": 88.9},
        },
    ]

    json_content = json.dumps(json_data, indent=2)

    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key="raw/logs_m2m.json",
        Body=json_content.encode("utf-8"),
    )
    print(" -> Archivo 'raw/logs_m2m.json' subido correctamente a S3.\n")


def cargar_y_perfilar_s3(file_key, is_json=False):
    """
    Descarga un objeto de S3 en memoria RAM y ejecuta un perfilamiento básico.

    Args:
        file_key (str): Ruta/Llave del objeto en S3.
        is_json (bool): Determina si el archivo debe procesarse como JSON.

    Returns:
        pd.DataFrame: DataFrame de Pandas cargado o None si hay error.
    """
    print("=" * 70)
    print(f"=== PASO 2: DESCARGA Y PERFILAMIENTO: {file_key} ===")
    print("=" * 70)

    try:
        # Descarga del objeto en memoria
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
        body = response["Body"].read()

        # Carga en DataFrame según el tipo de archivo
        if is_json:
            data_json = json.loads(body.decode("utf-8"))
            df = pd.json_normalize(data_json)
        else:
            df = pd.read_csv(io.BytesIO(body))

        # Impresión de perfilamiento
        print(f"\n1. Dimensiones (Filas, Columnas): {df.shape}")

        print("\n2. Tipos de datos por columna:")
        print(df.dtypes)

        print("\n3. Resumen estadístico:")
        print(df.describe().T)
        print("\n")

        return df

    except Exception as e:
        print(f"\n[ERROR] No se pudo procesar 's3://{BUCKET_NAME}/{file_key}': {e}\n")
        return None


if __name__ == "__main__":
    generar_y_subir_archivos_prueba()
    df_transacciones = cargar_y_perfilar_s3("raw/transacciones.csv")
    df_logs = cargar_y_perfilar_s3("raw/logs_m2m.json", is_json=True)
