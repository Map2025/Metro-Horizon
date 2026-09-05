import pyodbc
import pandas as pd
import warnings

warnings.filterwarnings('ignore', message='.*pandas only supports SQLAlchemy connectable.*')

class CicloChequesRepository:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def get_datos_cheques(self, fecha_desde: str, fecha_hasta: str) -> pd.DataFrame:
        """
        Obtiene los datos de cheques desde las tablas de Tesorería de Tango Gestión.
        Se filtran los cheques por el rango de fechas de ingreso y se excluyen los anulados.
        """
        query = """
        SELECT 
            c.N_INTERNO AS NumeroInterno,
            c.N_CHEQUE AS NumeroCheque,
            c.F_EMISION AS FechaEmision,
            c.FECHA_REC AS Fecha_Ingreso,
            c.FECHA_CHEQ AS Fecha_Vencimiento,
            c.IMPORTE_CH AS Importe,
            CASE 
                WHEN c.ESTADO = 'C' THEN 'En Cartera'
                WHEN c.ESTADO = 'R' THEN 'Rechazado'
                WHEN c.ESTADO IN ('N', 'X') THEN 'Anulado'
                ELSE 'Aplicado'
            END AS Estado,
            ISNULL(c.CLIENTE, 'SD') AS CodigoCliente,
            ISNULL(cli.RAZON_SOCI, 'Sin Cliente') AS RazonSocial,
            DATEDIFF(day, c.FECHA_REC, c.FECHA_CHEQ) AS Dias_Diferimiento,
            DATEDIFF(day, c.F_EMISION, c.FECHA_CHEQ) AS Dias_Emision_Vto
        FROM SBA14 c
        LEFT JOIN GVA14 cli ON c.CLIENTE = cli.COD_CLIENT
        WHERE c.ESTADO NOT IN ('N', 'X')
          AND c.FECHA_REC >= ? 
          AND c.FECHA_REC <= ?
        ORDER BY c.FECHA_REC ASC, c.N_INTERNO ASC
        """
        
        try:
            with pyodbc.connect(self.connection_string) as conn:
                df = pd.read_sql(query, conn, params=[fecha_desde, fecha_hasta])
                return df
        except Exception as e:
            print(f"Error al obtener datos de ciclo de cheques: {e}")
            # Devolver DataFrame vacío con la estructura esperada en caso de error
            return pd.DataFrame(columns=[
                'NumeroCheque', 'Fecha_Ingreso', 'Fecha_Vencimiento', 'Importe', 
                'Estado', 'CodigoCliente', 'RazonSocial', 'Dias_Diferimiento'
            ])
