import pandas as pd
import numpy as np

class GetRatioVentasUseCase:
    def __init__(self, repository):
        self.repo = repository

    def execute(self, fecha_desde: str, fecha_hasta: str):
        df_ventas = self.repo.get_ventas_mensuales(fecha_desde, fecha_hasta)
        df_cobranzas = self.repo.get_cobranzas_mensuales(fecha_desde, fecha_hasta)

        if df_ventas.empty and df_cobranzas.empty:
            return []

        df_ventas['Periodo'] = df_ventas['Anio'].astype(str) + '-' + df_ventas['Mes'].astype(str).str.zfill(2)
        df_cobranzas['Periodo'] = df_cobranzas['Anio'].astype(str) + '-' + df_cobranzas['Mes'].astype(str).str.zfill(2)

        df_merged = pd.merge(
            df_ventas[['Periodo', 'TotalVentas']], 
            df_cobranzas[['Periodo', 'TotalCobrado']], 
            on='Periodo', how='outer'
        ).fillna(0).sort_values('Periodo')
        
        # Avoid division by zero
        df_merged['Ratio (%)'] = (df_merged['TotalCobrado'] / df_merged['TotalVentas'] * 100)
        df_merged['Ratio (%)'] = df_merged['Ratio (%)'].replace([np.inf, -np.inf], 0).fillna(0).round(1)
        
        return df_merged.to_dict('records')
