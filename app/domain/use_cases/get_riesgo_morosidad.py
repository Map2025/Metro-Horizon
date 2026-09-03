import pandas as pd
from app.data.repositories.morosidad_repository import MorosidadRepository
from app.ml.services.morosidad_service import MorosidadService

class GetRiesgoMorosidadUseCase:
    def __init__(self, repository: MorosidadRepository, ml_service: MorosidadService):
        self.repository = repository
        self.ml_service = ml_service

    def execute(self) -> pd.DataFrame:
        # Extraer datos de la base de datos
        df_datos = self.repository.get_datos_morosidad()
        
        if df_datos.empty:
            return pd.DataFrame()
            
        # Calcular el score de riesgo utilizando el modelo predictivo
        df_resultados = self.ml_service.predecir_riesgo(df_datos)
        
        # Seleccionar las columnas para presentar en el reporte
        columnas_reporte = [
            'CodigoCliente', 'RazonSocial', 'SaldoActual', 
            'FechaUltimaFactura', 'FechaUltimoRecibo', 'Score_Riesgo', 'Nivel_Riesgo'
        ]
        
        # Ordenar por código de cliente
        df_resultados = df_resultados.sort_values(by='CodigoCliente')
        
        return df_resultados[columnas_reporte]
