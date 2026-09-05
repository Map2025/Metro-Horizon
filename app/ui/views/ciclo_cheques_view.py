import flet as ft
import datetime
from app.domain.use_cases.ciclo_cheques_service import ChequeAnalyticsService
import pandas as pd

class CicloChequesView(ft.Container):
    def __init__(self, service: ChequeAnalyticsService):
        super().__init__()
        self.service = service
        self.expand = True
        self.data_dict = {}
        
        # Filtros de Fecha
        today = datetime.datetime.now()
        start_date = (today - datetime.timedelta(days=365)).strftime('%d/%m/%y')
        end_date = today.strftime('%d/%m/%y')
        
        self.fecha_desde = ft.TextField(label="Ingreso Desde (DD/MM/AA)", value=start_date, width=180, read_only=True)
        self.date_picker_desde = ft.DatePicker(on_change=lambda e: self.cambio_fecha(e, self.fecha_desde))
        self.btn_cal_desde = ft.IconButton(icon=ft.icons.CALENDAR_MONTH, on_click=lambda e: self.date_picker_desde.pick_date())
        
        self.fecha_hasta = ft.TextField(label="Ingreso Hasta (DD/MM/AA)", value=end_date, width=180, read_only=True)
        self.date_picker_hasta = ft.DatePicker(on_change=lambda e: self.cambio_fecha(e, self.fecha_hasta))
        self.btn_cal_hasta = ft.IconButton(icon=ft.icons.CALENDAR_MONTH, on_click=lambda e: self.date_picker_hasta.pick_date())
        
        self.btn_analizar = ft.ElevatedButton("Ejecutar Análisis", on_click=self.ejecutar_analisis, icon=ft.icons.ANALYTICS, style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE))
        self.btn_limpiar = ft.OutlinedButton("Limpiar", on_click=self.limpiar_datos, icon=ft.icons.CLEAR)
        
        # Búsqueda en Tabla
        self.search_field = ft.TextField(
            label="Buscar Cliente", 
            prefix_icon=ft.icons.SEARCH, 
            on_change=self.filtrar_tabla,
            width=300
        )
        
        # Contenedores Dinámicos
        self.kpi_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)
        self.chart_container = ft.Container(height=300)
        self.table_container = ft.Column()
        
        # Layout Principal
        self.padding = 20
        self.content = ft.ListView([
            ft.Text("Ciclo de Permanencia y Liquidez de Cheques en Cartera", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
            ft.Divider(),
            ft.Row([
                self.fecha_desde, self.btn_cal_desde,
                self.fecha_hasta, self.btn_cal_hasta,
                self.btn_analizar,
                self.btn_limpiar
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Divider(),
            ft.Text("KPIs Consolidados", size=18, weight=ft.FontWeight.W_600),
            self.kpi_row,
            ft.Divider(),
            ft.Text("Proyección de Liquidez Futura (Cheques en Cartera)", size=18, weight=ft.FontWeight.W_600),
            self.chart_container,
            ft.Divider(),
            ft.Text("Ranking y Scoring de Clientes", size=18, weight=ft.FontWeight.W_600),
            self.search_field,
            self.table_container
        ], expand=True, spacing=10)

    def did_mount(self):
        if self.date_picker_desde not in self.page.overlay:
            self.page.overlay.append(self.date_picker_desde)
        if self.date_picker_hasta not in self.page.overlay:
            self.page.overlay.append(self.date_picker_hasta)
        self.page.update()

    def cambio_fecha(self, e, text_field):
        if e.control.value:
            text_field.value = e.control.value.strftime('%d/%m/%y')
            self.update()

    def limpiar_datos(self, e):
        self.data_dict = {}
        self.kpi_row.controls.clear()
        self.chart_container.content = None
        self.table_container.controls.clear()
        self.search_field.value = ""
        
        today = datetime.datetime.now()
        self.fecha_desde.value = (today - datetime.timedelta(days=365)).strftime('%d/%m/%y')
        self.fecha_hasta.value = today.strftime('%d/%m/%y')
        self.update()

    def ejecutar_analisis(self, e):
        try:
            fd = datetime.datetime.strptime(self.fecha_desde.value, '%d/%m/%y').strftime('%Y%m%d')
            fh = datetime.datetime.strptime(self.fecha_hasta.value, '%d/%m/%y').strftime('%Y%m%d')
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Formato de fecha inválido."), bgcolor=ft.colors.RED)
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        self.data_dict = self.service.get_analytics(fd, fh)
        self.renderizar_kpis()
        self.renderizar_grafico()
        self.renderizar_tabla()

    def renderizar_kpis(self):
        kpis = self.data_dict.get('kpis', {})
        total_cartera = kpis.get('total_activo_cartera', 0.0)
        plazo_ponderado = kpis.get('plazo_ponderado_global', 0.0)
        tasa_rechazo = kpis.get('tasa_rechazo_global', 0.0)
        
        def crear_kpi_card(titulo, valor, icono, color):
            return ft.Card(
                elevation=4,
                content=ft.Container(
                    padding=20,
                    width=280,
                    content=ft.Row([
                        ft.Icon(icono, size=40, color=color),
                        ft.Column([
                            ft.Text(titulo, size=14, color=ft.colors.GREY_700),
                            ft.Text(valor, size=20, weight=ft.FontWeight.BOLD)
                        ], spacing=2)
                    ])
                )
            )
            
        self.kpi_row.controls = [
            crear_kpi_card("Total Activo en Cartera", f"${total_cartera:,.2f}", ft.icons.ACCOUNT_BALANCE_WALLET, ft.colors.BLUE_600),
            crear_kpi_card("Plazo Prom. Ponderado", f"{plazo_ponderado:.1f} días", ft.icons.TIMELAPSE, ft.colors.ORANGE_600),
            crear_kpi_card("Tasa Rechazo Global", f"{tasa_rechazo:.1f}%", ft.icons.WARNING_AMBER_ROUNDED, ft.colors.RED_600)
        ]
        self.update()

    def renderizar_grafico(self):
        proy = self.data_dict.get('proyeccion_liquidez', {})
        df_grafico = proy.get('grafico_vencimientos', pd.DataFrame())
        
        if df_grafico.empty:
            self.chart_container.content = ft.Text("No hay cheques en cartera para proyectar.", color=ft.colors.GREY_500)
            self.update()
            return
            
        chart_data = []
        max_y = float(df_grafico['Importe'].max())
        labels = []
        
        for idx, (_, row) in enumerate(df_grafico.iterrows()):
            chart_data.append(
                ft.BarChartGroup(
                    x=idx,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0, 
                            to_y=float(row['Importe']), 
                            width=30, 
                            color=ft.colors.TEAL_400,
                            tooltip=f"{row['MesVencimiento']}\nImporte: ${float(row['Importe']):,.2f}"
                        )
                    ]
                )
            )
            labels.append(ft.ChartAxisLabel(value=float(idx), label=ft.Text(str(row['MesVencimiento']), size=10)))
            
        self.chart_container.content = ft.BarChart(
            bar_groups=chart_data,
            bottom_axis=ft.ChartAxis(labels=labels),
            max_y=max_y * 1.1 if max_y > 0 else 100,
            tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.GREY_800)
        )
        self.update()

    def obtener_color_score(self, score):
        if score == "Rápido": return ft.colors.GREEN_600
        if score == "Medio": return ft.colors.ORANGE_500
        if score == "Lento": return ft.colors.RED_400
        if score == "Alto Riesgo": return ft.colors.RED_900
        return ft.colors.GREY_500

    def renderizar_tabla(self, query=""):
        df_ranking = self.data_dict.get('ranking_clientes', pd.DataFrame())
        
        if df_ranking.empty:
            self.table_container.controls = [ft.Text("No hay datos para mostrar.", color=ft.colors.GREY_500)]
            self.update()
            return
            
        if query:
            df_ranking = df_ranking[df_ranking['RazonSocial'].str.contains(query, case=False, na=False)]
            
        rows = []
        for _, row in df_ranking.iterrows():
            score = row['Score']
            color_score = self.obtener_color_score(score)
            
            # Semáforo visual
            semaforo = ft.Container(
                width=12, height=12, border_radius=6, bgcolor=color_score,
                tooltip=f"Score: {score}"
            )
            
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(row['RazonSocial']))),
                ft.DataCell(
                    ft.Text(f"${float(row['ImporteTotal']):,.2f}", color=ft.colors.BLUE_700, weight=ft.FontWeight.BOLD, tooltip="Click para ver detalle"),
                    on_tap=lambda e, cod=row['CodigoCliente']: self.mostrar_detalle_cheques(cod)
                ),
                ft.DataCell(ft.Text(f"{float(row['DiasPonderados']):.0f}")),
                ft.DataCell(ft.Text(f"{float(row['TasaRechazo']):.2f}%")),
                ft.DataCell(ft.Row([semaforo, ft.Text(str(score), color=color_score, weight=ft.FontWeight.W_600)])),
            ]))
            
        tabla = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Cliente / Razón Social")),
                ft.DataColumn(ft.Text("Importe Operado ($)"), numeric=True),
                ft.DataColumn(ft.Text("Días Prom. Ponderado"), numeric=True),
                ft.DataColumn(ft.Text("Tasa Rechazo (%)"), numeric=True),
                ft.DataColumn(ft.Text("Scoring Liquidez")),
            ],
            rows=rows,
            heading_row_color=ft.colors.GREY_100,
            show_checkbox_column=False
        )
        
        self.table_container.controls = [tabla]
        self.update()

    def filtrar_tabla(self, e):
        self.renderizar_tabla(query=self.search_field.value)

    def mostrar_detalle_cheques(self, cod_cliente):
        detalle_cheques = self.data_dict.get('detalle_cheques', [])
        
        # Filtrar por cliente
        cheques_filtrados = [c for c in detalle_cheques if c['CodigoCliente'] == cod_cliente]
        
        if not cheques_filtrados:
            return
            
        razon_social = cheques_filtrados[0].get('RazonSocial', 'Cliente')
            
        rows = []
        for c in cheques_filtrados:
            n_interno = str(c.get('NumeroInterno', ''))
            # Format numbers safely avoiding nan showing as "nan"
            if n_interno == 'nan' or not n_interno: n_interno = ""
            elif '.' in n_interno: n_interno = n_interno.split('.')[0]
                
            n_cheque = str(c.get('NumeroCheque', ''))
            if n_cheque == 'nan' or not n_cheque: n_cheque = ""
            elif '.' in n_cheque: n_cheque = n_cheque.split('.')[0]
                
            fecha_origen = c.get('FechaEmision_str', '')
            fecha_cheque = c.get('FechaVencimiento_str', '')
            importe = float(c.get('Importe', 0.0))
            estado = str(c.get('Estado', ''))
            
            dias_vto = str(c.get('Dias_Emision_Vto', ''))
            if dias_vto == 'nan': dias_vto = '-'
            elif '.' in dias_vto: dias_vto = dias_vto.split('.')[0]
            
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(n_interno)),
                ft.DataCell(ft.Text(n_cheque)),
                ft.DataCell(ft.Text(fecha_origen)),
                ft.DataCell(ft.Text(fecha_cheque)),
                ft.DataCell(ft.Text(estado)),
                ft.DataCell(ft.Text(f"${importe:,.2f}")),
                ft.DataCell(ft.Text(dias_vto)),
            ]))
            
        tabla_detalle = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nº Interno")),
                ft.DataColumn(ft.Text("Nº Cheque")),
                ft.DataColumn(ft.Text("F. Emisión")),
                ft.DataColumn(ft.Text("F. Vencimiento")),
                ft.DataColumn(ft.Text("Estado")),
                ft.DataColumn(ft.Text("Importe ($)"), numeric=True),
                ft.DataColumn(ft.Text("Días"), numeric=True),
            ],
            rows=rows,
            heading_row_color=ft.colors.GREY_100,
            column_spacing=30
        )
        
        contenedor_tabla = ft.Row([tabla_detalle], scroll=ft.ScrollMode.AUTO)
        
        dlg = ft.AlertDialog(
            title=ft.Text(f"Detalle de Cheques - {razon_social}"),
            content=ft.Column([contenedor_tabla], scroll=ft.ScrollMode.AUTO, height=400, width=900),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self.cerrar_dialog(dlg))]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def cerrar_dialog(self, dlg):
        dlg.open = False
        self.page.update()
