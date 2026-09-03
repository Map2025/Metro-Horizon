import pandas as pd
import pyodbc

class VentasRepository:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def get_ventas_mensuales(self, fecha_desde: str, fecha_hasta: str) -> pd.DataFrame:
        query = """
        SELECT 
            YEAR(FECHA_EMIS) as Anio, 
            MONTH(FECHA_EMIS) as Mes, 
            SUM(CASE WHEN T_COMP IN ('FAC', 'ND ') THEN IMPORTE ELSE -IMPORTE END) as TotalVentas
        FROM GVA12
        WHERE T_COMP IN ('FAC', 'ND ', 'NC ')
          AND ESTADO != 'ANU'
          AND FECHA_EMIS >= ? AND FECHA_EMIS <= ?
        GROUP BY YEAR(FECHA_EMIS), MONTH(FECHA_EMIS)
        ORDER BY Anio, Mes
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                return pd.read_sql(query, conn, params=[fecha_desde, fecha_hasta])
        except Exception as e:
            print(f"Error en get_ventas_mensuales: {e}")
            return pd.DataFrame()

    def get_cobranzas_mensuales(self, fecha_desde: str, fecha_hasta: str) -> pd.DataFrame:
        query = """
        SELECT 
            YEAR(S4.FECHA) as Anio, 
            MONTH(S4.FECHA) as Mes, 
            SUM(S5.MONTO) as TotalCobrado
        FROM SBA05 S5
        INNER JOIN SBA04 S4 ON S5.N_COMP = S4.N_COMP AND S5.COD_COMP = S4.COD_COMP
        WHERE S4.SITUACION = 'N' 
          AND S5.COD_CTA = 11030101.0
          AND S5.D_H = 'H'
          AND S4.FECHA >= ? AND S4.FECHA <= ?
        GROUP BY YEAR(S4.FECHA), MONTH(S4.FECHA)
        ORDER BY Anio, Mes
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                return pd.read_sql(query, conn, params=[fecha_desde, fecha_hasta])
        except Exception as e:
            print(f"Error en get_cobranzas_mensuales: {e}")
            return pd.DataFrame()
