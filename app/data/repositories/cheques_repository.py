import pyodbc
import pandas as pd
import warnings

warnings.filterwarnings('ignore', message='.*pandas only supports SQLAlchemy connectable.*')

class ChequesRepository:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def get_cheques_en_cartera(self, fecha_desde: str = None, fecha_hasta: str = None) -> pd.DataFrame:
        query = """
        SELECT 
            S.N_INTERNO AS NumeroInterno,
            S.N_CHEQUE AS NumeroCheque,
            S.CLIENTE AS Cliente,
            C.RAZON_SOCI AS RazonSocial,
            S.FECHA_CHEQ AS FechaCheque,
            S.IMPORTE_CH AS Importe
        FROM SBA14 S
        LEFT JOIN GVA14 C ON S.CLIENTE = C.COD_CLIENT
        WHERE S.ESTADO = 'C'
        """
        
        params = []
        if fecha_desde:
            query += " AND S.FECHA_CHEQ >= ?"
            params.append(fecha_desde)
        if fecha_hasta:
            query += " AND S.FECHA_CHEQ <= ?"
            params.append(fecha_hasta)
            
        try:
            with pyodbc.connect(self.connection_string) as conn:
                if params:
                    return pd.read_sql(query, conn, params=params)
                else:
                    return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Error al obtener cheques en cartera: {e}")
            return pd.DataFrame(columns=['NumeroInterno', 'NumeroCheque', 'Cliente', 'FechaCheque', 'Importe'])
