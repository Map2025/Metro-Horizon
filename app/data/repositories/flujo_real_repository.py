import pyodbc
import pandas as pd
import warnings

warnings.filterwarnings('ignore', message='.*pandas only supports SQLAlchemy connectable.*')

class FlujoRealRepository:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def get_saldo_inicial(self, fecha_desde: str) -> float:
        """
        Calcula el saldo inicial real de las cuentas de liquidez (1101%) 
        justo antes de la fecha_desde.
        """
        query = """
        SELECT 
            SUM(CASE WHEN S5.D_H = 'D' THEN S5.MONTO ELSE 0 END) -
            SUM(CASE WHEN S5.D_H = 'H' THEN S5.MONTO ELSE 0 END) AS SaldoInicial
        FROM SBA05 S5
        WHERE S5.COD_CTA >= 11010000 AND S5.COD_CTA < 11020000
          AND S5.FECHA < ?
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                df = pd.read_sql(query, conn, params=[fecha_desde])
                val = float(df['SaldoInicial'].iloc[0]) if not df.empty and pd.notna(df['SaldoInicial'].iloc[0]) else 0.0
                return val
        except Exception as e:
            with open('error.log', 'a') as f_err:
                f_err.write(f"Error getting saldo inicial: {e}")
            return 0.0

    def get_movimientos_tesoreria(self, fecha_desde: str, fecha_hasta: str) -> pd.DataFrame:
        """
        Obtiene los movimientos de tesorería en un rango de fechas.
        Retorna tanto las cuentas de liquidez como las contracuentas involucradas
        en esos mismos comprobantes.
        """
        query = """
        SELECT 
            S5.FECHA,
            S5.N_COMP,
            S5.D_H,
            S5.MONTO,
            S5.COD_CTA,
            S1.DESCRIPCIO,
            P.NOM_PROVEE AS NOMBRE_PROVEEDOR,
            C.RAZON_SOCI AS NOMBRE_CLIENTE
        FROM SBA05 S5
        LEFT JOIN SBA01 S1 ON S5.COD_CTA = S1.COD_CTA
        LEFT JOIN CPA01 P ON S5.COD_CPA01 COLLATE DATABASE_DEFAULT = P.COD_PROVEE COLLATE DATABASE_DEFAULT
        LEFT JOIN GVA14 C ON S5.COD_GVA14 COLLATE DATABASE_DEFAULT = C.COD_CLIENT COLLATE DATABASE_DEFAULT
        WHERE S5.FECHA >= ? AND S5.FECHA <= ?
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                return pd.read_sql(query, conn, params=[fecha_desde, fecha_hasta])
        except Exception as e:
            with open('error.log', 'a') as f_err:
                f_err.write(f"Error getting movimientos: {e}")
            return pd.DataFrame(columns=['FECHA', 'N_COMP', 'D_H', 'MONTO', 'COD_CTA', 'DESCRIPCIO'])
