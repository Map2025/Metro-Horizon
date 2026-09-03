import pyodbc
import pandas as pd
import warnings

# Suprimir el warning de pandas sobre pyodbc
warnings.filterwarnings('ignore', message='.*pandas only supports SQLAlchemy connectable.*')

class MorosidadRepository:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def get_datos_morosidad(self) -> pd.DataFrame:
        # Obtenemos el saldo consolidado por cliente y su último recibo
        query = """
        SELECT 
            C.COD_CLIENT AS CodigoCliente,
            C.RAZON_SOCI AS RazonSocial,
            SUM(CASE WHEN F.T_COMP IN ('FAC', 'NDB', 'NDI') THEN F.IMPORTE ELSE 0 END) -
            SUM(CASE WHEN F.T_COMP IN ('REC', 'NCD', 'NCI') THEN F.IMPORTE ELSE 0 END) AS SaldoActual,
            MAX(CASE WHEN F.T_COMP = 'REC' THEN F.FECHA_EMIS ELSE NULL END) AS FechaUltimoRecibo,
            MIN(CASE WHEN F.T_COMP = 'FAC' THEN F.FECHA_EMIS ELSE NULL END) AS FechaPrimeraFactura,
            MAX(CASE WHEN F.T_COMP = 'FAC' THEN F.FECHA_EMIS ELSE NULL END) AS FechaUltimaFactura
        FROM 
            GVA14 C
        INNER JOIN 
            GVA12 F ON C.COD_CLIENT = F.COD_CLIENT
        GROUP BY 
            C.COD_CLIENT, C.RAZON_SOCI
        HAVING 
            (SUM(CASE WHEN F.T_COMP IN ('FAC', 'NDB', 'NDI') THEN F.IMPORTE ELSE 0 END) -
             SUM(CASE WHEN F.T_COMP IN ('REC', 'NCD', 'NCI') THEN F.IMPORTE ELSE 0 END)) > 1
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            print(f"Error al conectar a la BD: {e}")
            return pd.DataFrame()
