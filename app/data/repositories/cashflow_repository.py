import pyodbc
import pandas as pd
import warnings

warnings.filterwarnings('ignore', message='.*pandas only supports SQLAlchemy connectable.*')

class CashFlowRepository:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def get_cheques_terceros_cartera(self) -> pd.DataFrame:
        # SBA14: Cheques de terceros en cartera
        query = "SELECT FECHA_CHEQ as FechaVencimiento, IMPORTE_CH as Importe FROM SBA14 WHERE ESTADO = 'C'"
        try:
            with pyodbc.connect(self.connection_string) as conn:
                return pd.read_sql(query, conn)
        except Exception:
            return pd.DataFrame(columns=['FechaVencimiento', 'Importe'])

    def get_cheques_propios_diferidos(self) -> pd.DataFrame:
        # SBA15: Cheques diferidos propios. Consideramos los no cobrados/anulados (Ej. ESTADO = 'E' Emitidos)
        query = """
        SELECT FECHA_CHEQ as FechaVencimiento, IMPORTE_CH as Importe 
        FROM SBA15 
        WHERE ESTADO NOT IN ('D', 'A', 'R') 
          AND FECHA_CHEQ >= GETDATE()
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                return pd.read_sql(query, conn)
        except Exception:
            return pd.DataFrame(columns=['FechaVencimiento', 'Importe'])

    def get_deuda_proveedores(self) -> float:
        # CPA04: Comprobantes de compras. 
        # La deuda se refleja negativa. FAC y ND aumentan deuda (la hacen más negativa en el sistema)
        # y OP y NC la reducen.
        query = """
        SELECT 
            SUM(CASE WHEN T_COMP IN ('FAC', 'NDB', 'NDI') THEN IMPORTE ELSE 0 END) -
            SUM(CASE WHEN T_COMP IN ('O/P', 'NCD', 'NCI') THEN IMPORTE ELSE 0 END) AS SaldoAcreedor
        FROM CPA04
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                df = pd.read_sql(query, conn)
                val = float(df['SaldoAcreedor'].iloc[0]) if not df.empty and pd.notna(df['SaldoAcreedor'].iloc[0]) else 0.0
                # Retornamos valor absoluto de la deuda
                return abs(val) if val > 0 else 0.0 
        except Exception:
            return 0.0

    def get_deuda_clientes_detalle(self) -> pd.DataFrame:
        # GVA14 y GVA12: Deuda por cliente
        query = """
        SELECT 
            C.COD_CLIENT AS CodigoCliente,
            C.RAZON_SOCI AS RazonSocial,
            SUM(CASE WHEN T_COMP IN ('FAC', 'NDB', 'NDI') THEN IMPORTE ELSE 0 END) -
            SUM(CASE WHEN T_COMP IN ('REC', 'NCD', 'NCI') THEN IMPORTE ELSE 0 END) AS SaldoDeudor
        FROM GVA12 F
        INNER JOIN GVA14 C ON F.COD_CLIENT = C.COD_CLIENT
        GROUP BY C.COD_CLIENT, C.RAZON_SOCI
        HAVING (SUM(CASE WHEN T_COMP IN ('FAC', 'NDB', 'NDI') THEN IMPORTE ELSE 0 END) -
                SUM(CASE WHEN T_COMP IN ('REC', 'NCD', 'NCI') THEN IMPORTE ELSE 0 END)) > 1
        ORDER BY SaldoDeudor DESC
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                return pd.read_sql(query, conn)
        except Exception:
            return pd.DataFrame()
            
    def get_saldo_bancos_caja(self) -> float:
        # Saldo en cuentas monetarias a través de SBA05
        # NOTA: En un entorno real se filtraría por COD_CTA correspondiente a bancos (Ej: uniendo con SBA02)
        query = """
        SELECT 
            SUM(CASE WHEN D_H = 'D' THEN MONTO ELSE 0 END) -
            SUM(CASE WHEN D_H = 'H' THEN MONTO ELSE 0 END) AS SaldoLiquidez
        FROM SBA05
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                df = pd.read_sql(query, conn)
                val = float(df['SaldoLiquidez'].iloc[0]) if not df.empty and pd.notna(df['SaldoLiquidez'].iloc[0]) else 0.0
                return abs(val) # Forzamos absoluto por si el balanceo D/H está invertido globalmente
        except Exception:
            return 0.0
