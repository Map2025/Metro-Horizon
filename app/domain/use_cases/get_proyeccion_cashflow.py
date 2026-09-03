import pandas as pd
import numpy as np
import datetime
from app.data.repositories.cashflow_repository import CashFlowRepository
from app.data.repositories.morosidad_repository import MorosidadRepository
from app.ml.services.morosidad_service import MorosidadService

class GetProyeccionCashFlowUseCase:
    def __init__(self, repo_cf: CashFlowRepository, repo_morosidad: MorosidadRepository, ml_service: MorosidadService):
        self.repo_cf = repo_cf
        self.repo_morosidad = repo_morosidad
        self.ml_service = ml_service

    def execute(self) -> dict:
        hoy = pd.Timestamp.today().normalize()
        
        # 1. Obtener Liquidez Inicial (Día 0)
        saldo_bancos = self.repo_cf.get_saldo_bancos_caja()
        df_cheques_terceros = self.repo_cf.get_cheques_terceros_cartera()
        
        cheques_al_dia = 0
        if not df_cheques_terceros.empty:
            df_cheques_terceros['FechaVencimiento'] = pd.to_datetime(df_cheques_terceros['FechaVencimiento'])
            # No considerar los cheques que vencen a más de 30 días
            df_cheques_terceros = df_cheques_terceros[df_cheques_terceros['FechaVencimiento'] <= hoy + pd.Timedelta(days=30)]
            cheques_al_dia = df_cheques_terceros.loc[df_cheques_terceros['FechaVencimiento'] <= hoy, 'Importe'].sum()
            
        liquidez_inicial = saldo_bancos + cheques_al_dia

        # 2. Egresos Proyectados
        deuda_proveedores = self.repo_cf.get_deuda_proveedores()
        df_cheques_propios = self.repo_cf.get_cheques_propios_diferidos()

        # 3. Ingresos Proyectados (Ajustados por ML)
        df_clientes_raw = self.repo_morosidad.get_datos_morosidad()
        if not df_clientes_raw.empty:
            df_clientes_riesgo = self.ml_service.predecir_riesgo(df_clientes_raw)
        else:
            df_clientes_riesgo = pd.DataFrame(columns=['CodigoCliente', 'RazonSocial', 'SaldoActual', 'Nivel_Riesgo'])

        if not df_clientes_riesgo.empty:
            df_clientes_riesgo['Ingreso_Semana1'] = np.where(df_clientes_riesgo['Nivel_Riesgo'] == 'Bajo', df_clientes_riesgo['SaldoActual'] * 0.60, 0)
            df_clientes_riesgo['Ingreso_Semana2'] = np.where(df_clientes_riesgo['Nivel_Riesgo'] == 'Bajo', df_clientes_riesgo['SaldoActual'] * 0.40, 0)
            df_clientes_riesgo['Ingreso_Semana3'] = np.where(df_clientes_riesgo['Nivel_Riesgo'] == 'Medio', df_clientes_riesgo['SaldoActual'] * 0.50, 0)
            df_clientes_riesgo['Ingreso_Semana4'] = np.where(df_clientes_riesgo['Nivel_Riesgo'] == 'Medio', df_clientes_riesgo['SaldoActual'] * 0.50,
                                                    np.where(df_clientes_riesgo['Nivel_Riesgo'] == 'Alto', df_clientes_riesgo['SaldoActual'] * 0.20, 0))
                                                    
            ingresos_semanas = [
                df_clientes_riesgo['Ingreso_Semana1'].sum(),
                df_clientes_riesgo['Ingreso_Semana2'].sum(),
                df_clientes_riesgo['Ingreso_Semana3'].sum(),
                df_clientes_riesgo['Ingreso_Semana4'].sum()
            ]
        else:
            ingresos_semanas = [0, 0, 0, 0]

        # CREACIÓN DEL FLUJO
        datos_flujo = []
        saldo_acumulado = liquidez_inicial
        
        datos_flujo.append({
            'Periodo': 'Hoy (Liquidez Inicial)',
            'Ingresos': cheques_al_dia,
            'Egresos': 0,
            'Saldo Acumulado': saldo_acumulado,
            'ColumnaDetalle': 'Liquidez'
        })

        dist_proveedores = [0.40, 0.30, 0.20, 0.10] 

        for i in range(4):
            fecha_inicio = hoy + pd.Timedelta(days=i*7)
            fecha_fin = hoy + pd.Timedelta(days=(i+1)*7)
            
            # Sumar cheques de terceros que vencen en esta semana
            ingreso_cheques_dif = 0
            if not df_cheques_terceros.empty:
                mask_ch_in = (df_cheques_terceros['FechaVencimiento'] > fecha_inicio) & (df_cheques_terceros['FechaVencimiento'] <= fecha_fin)
                ingreso_cheques_dif = df_cheques_terceros.loc[mask_ch_in, 'Importe'].sum()
                
            ingreso_est = ingresos_semanas[i] + ingreso_cheques_dif
            
            egreso_est_prov = deuda_proveedores * dist_proveedores[i]
            
            egreso_cheques = 0
            if not df_cheques_propios.empty:
                df_cheques_propios['FechaVencimiento'] = pd.to_datetime(df_cheques_propios['FechaVencimiento'])
                mask_ch_out = (df_cheques_propios['FechaVencimiento'] >= fecha_inicio) & (df_cheques_propios['FechaVencimiento'] < fecha_fin)
                egreso_cheques = df_cheques_propios.loc[mask_ch_out, 'Importe'].sum()
                
            egreso_total = egreso_est_prov + egreso_cheques
            saldo_acumulado = saldo_acumulado + ingreso_est - egreso_total
            
            datos_flujo.append({
                'Periodo': f'Semana {i+1}',
                'Ingresos': ingreso_est,
                'Egresos': egreso_total,
                'Saldo Acumulado': saldo_acumulado,
                'ColumnaDetalle': f'Ingreso_Semana{i+1}'
            })

        return {
            'flujo': pd.DataFrame(datos_flujo),
            'clientes_detalle': df_clientes_riesgo,
            'cheques_terceros': cheques_al_dia,
            'df_cheques_terceros': df_cheques_terceros
        }
