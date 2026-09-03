import pandas as pd
from app.data.repositories.flujo_real_repository import FlujoRealRepository

class GetFlujoRealUseCase:
    def __init__(self, repo_flujo_real: FlujoRealRepository):
        self.repo = repo_flujo_real

    def execute(self, fecha_desde_str: str, fecha_hasta_str: str) -> dict:
        fecha_desde = pd.to_datetime(fecha_desde_str)
        fecha_hasta = pd.to_datetime(fecha_hasta_str)
        diferencia_dias = (fecha_hasta - fecha_desde).days

        # 1. Obtener Saldo Inicial (ignorado por requerimiento, solo flujo del período)
        saldo_inicial = 0.0
        
        # 2. Obtener Movimientos
        df_mov = self.repo.get_movimientos_tesoreria(fecha_desde_str, fecha_hasta_str)
        
        if df_mov.empty:
            return {
                'flujo': pd.DataFrame(),
                'detalle': pd.DataFrame(),
                'saldo_inicial': saldo_inicial,
                'periodos': []
            }
            
        df_mov['FECHA'] = pd.to_datetime(df_mov['FECHA'])
        df_mov['COD_CTA_STR'] = df_mov['COD_CTA'].astype(str)
        cuentas_excluidas = ['11010102.0', '11010103.0', '11010114.0']
        df_mov['IS_LIQ'] = df_mov['COD_CTA_STR'].str.startswith('1101') & ~df_mov['COD_CTA_STR'].isin(cuentas_excluidas)
        
        # 3. Filtrar comprobantes que mueven liquidez
        vouchers_with_liq = df_mov[df_mov['IS_LIQ']]['N_COMP'].unique()
        df_valid = df_mov[df_mov['N_COMP'].isin(vouchers_with_liq)].copy()
        
        # 4. Calcular el Cash Impact a partir de las contracuentas
        # Si no hay contracuentas (transf. interna de liquidez), el impacto neto será 0 si sumamos todo, 
        # pero es mejor ignorarlo analíticamente o dejarlo descartado.
        df_non_liq = df_valid[~df_valid['IS_LIQ']].copy()
        
        if df_non_liq.empty:
            return {
                'flujo': pd.DataFrame(),
                'detalle': pd.DataFrame(),
                'saldo_inicial': saldo_inicial,
                'periodos': []
            }
            
        # Renombrar conceptos de cheques/valores para claridad (reflejando la acreditación bancaria)
        mapeo_nombres = {
            'VALORES A DEPOSITAR': 'Acreditación / Depósito de Valores',
            'VALORES A DEPOSITAR -echeq-': 'Acreditación / Depósito de E-Cheqs',
            'CHEQUE DE 3ROS': 'Acreditación / Depósito Cheques de 3ros'
        }
        df_non_liq['DESCRIPCIO'] = df_non_liq['DESCRIPCIO'].replace(mapeo_nombres)
        
        df_non_liq['CASH_IMPACT'] = df_non_liq.apply(
            lambda r: float(r['MONTO']) if r['D_H'] == 'H' else -float(r['MONTO']), 
            axis=1
        )
        
        # 5. Agrupar por período
        es_mensual = diferencia_dias > 35
        
        def asignar_periodo(fecha):
            if es_mensual:
                return fecha.strftime('%Y-%m')
            else:
                # Calcular semana del mes o semana genérica
                dias_transcurridos = (fecha - fecha_desde).days
                semana = (dias_transcurridos // 7) + 1
                return f"Semana {semana}"
                
        df_non_liq['PERIODO'] = df_non_liq['FECHA'].apply(asignar_periodo)
        
        # 6. Preparar Tabla Analítica (Concepto x Período)
        # Ingresos (CASH_IMPACT > 0) y Egresos (CASH_IMPACT < 0)
        df_non_liq['TIPO'] = df_non_liq['CASH_IMPACT'].apply(lambda x: 'Ingreso' if x > 0 else 'Egreso')
        
        # Detalle para Drill-down (enviamos todo el dataframe de contracuentas)
        df_detalle = df_non_liq.copy()
        
        # Agrupación para la tabla resumen
        # Pivot table: Indice = DESCRIPCIO, Columnas = PERIODO, Valores = CASH_IMPACT
        df_pivot = pd.pivot_table(
            df_non_liq, 
            values='CASH_IMPACT', 
            index=['TIPO', 'DESCRIPCIO'], 
            columns=['PERIODO'], 
            aggfunc='sum', 
            fill_value=0
        ).reset_index()
        
        # Calcular los saldos por período para la tabla de KPIs y Gráficos
        periodos_ordenados = sorted(df_non_liq['PERIODO'].unique())
        
        datos_periodo = []
        saldo_acumulado = saldo_inicial
        
        for p in periodos_ordenados:
            df_p = df_non_liq[df_non_liq['PERIODO'] == p]
            ingresos = df_p[df_p['CASH_IMPACT'] > 0]['CASH_IMPACT'].sum()
            egresos = abs(df_p[df_p['CASH_IMPACT'] < 0]['CASH_IMPACT'].sum())
            flujo_neto = ingresos - egresos
            saldo_acumulado += flujo_neto
            
            datos_periodo.append({
                'Periodo': p,
                'Ingresos': ingresos,
                'Egresos': egresos,
                'Flujo Neto': flujo_neto,
                'Saldo Acumulado': saldo_acumulado
            })
            
        # Resumen por cuenta de liquidez
        df_liq = df_mov[df_mov['IS_LIQ']].copy()
        if not df_liq.empty:
            df_liq['MontoNeto'] = df_liq.apply(lambda r: float(r['MONTO']) if r['D_H'] == 'D' else -float(r['MONTO']), axis=1)
            resumen_cuentas = df_liq.groupby('DESCRIPCIO')['MontoNeto'].sum().reset_index()
            resumen_cuentas.columns = ['Cuenta', 'Neto']
            resumen_cuentas = resumen_cuentas[resumen_cuentas['Neto'] != 0].sort_values(by='Neto', ascending=False)
        else:
            resumen_cuentas = pd.DataFrame(columns=['Cuenta', 'Neto'])

        return {
            'flujo_kpi': pd.DataFrame(datos_periodo),
            'pivot_conceptos': df_pivot,
            'detalle_movimientos': df_detalle,
            'saldo_inicial': saldo_inicial,
            'periodos': periodos_ordenados,
            'resumen_cuentas': resumen_cuentas
        }
