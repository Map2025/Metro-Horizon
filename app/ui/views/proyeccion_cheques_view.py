import flet as ft
from app.domain.use_cases.get_proyeccion_cheques_use_case import GetProyeccionChequesUseCase
import pandas as pd
import datetime

class ProyeccionChequesView(ft.Container):
    def __init__(self, use_case: GetProyeccionChequesUseCase):
        super().__init__()
        self.use_case = use_case
        self.expand = True
        self.dict_resultados = {}
        self.modo_actual = "semana" # "semana" o "mes"
        
        # Date Pickers
        self.date_picker_desde = ft.DatePicker(
            on_change=lambda e: self.cambio_fecha(e, self.fecha_desde)
        )
        self.date_picker_hasta = ft.DatePicker(
            on_change=lambda e: self.cambio_fecha(e, self.fecha_hasta)
        )
        
        # Filtros
        # Inicializamos con el año actual o algún rango razonable
        today = datetime.datetime.now()
        start_date = today.strftime('%d/%m/%y')
        end_date = (today + datetime.timedelta(days=90)).strftime('%d/%m/%y')
        
        self.fecha_desde = ft.TextField(label="Desde (DD/MM/AA)", value=start_date, width=150, read_only=True)
        self.btn_cal_desde = ft.IconButton(icon=ft.icons.CALENDAR_MONTH, on_click=lambda e: self.date_picker_desde.pick_date())
        
        self.fecha_hasta = ft.TextField(label="Hasta (DD/MM/AA)", value=end_date, width=150, read_only=True)
        self.btn_cal_hasta = ft.IconButton(icon=ft.icons.CALENDAR_MONTH, on_click=lambda e: self.date_picker_hasta.pick_date())
        
        self.btn_generar = ft.ElevatedButton("Generar Proyección", on_click=self.actualizar_datos, icon=ft.icons.PLAY_ARROW)
        self.btn_limpiar = ft.OutlinedButton("Limpiar", on_click=self.limpiar_datos, icon=ft.icons.CLEAR)
        
        # Tabs para elegir Semana / Mes
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Agrupado por Semana"),
                ft.Tab(text="Agrupado por Mes"),
            ],
            on_change=self.cambiar_modo
        )
        
        # KPI Totales
        self.txt_total_cartera = ft.Text("$ 0.00", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700)
        self.kpi_card = ft.Card(
            content=ft.Container(
                content=ft.Column([ft.Text("Total en Cartera en el periodo", size=14, color=ft.colors.GREY_700), self.txt_total_cartera]),
                padding=20,
                width=300
            )
        )
        
        # Contenedores para Gráfico y Tabla
        self.chart_container = ft.Container(height=350, expand=True)
        self.data_table_container = ft.Container(content=ft.Text("Genera la proyección para ver el detalle.", color=ft.colors.GREY_500))
        
        self.content = ft.Column([
            ft.Text("Proyección Cartera de Cheques", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([
                self.fecha_desde, self.btn_cal_desde,
                self.fecha_hasta, self.btn_cal_hasta, 
                self.btn_generar, self.btn_limpiar
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Divider(),
            self.kpi_card,
            self.tabs,
            ft.Row([self.chart_container]),
            ft.Divider(),
            ft.Text("Resumen Agrupado (Click para ver detalle)", size=18, weight=ft.FontWeight.BOLD),
            self.data_table_container
        ], scroll=ft.ScrollMode.AUTO, expand=True)

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
        self.fecha_desde.value = ""
        self.fecha_hasta.value = ""
        self.txt_total_cartera.value = "$ 0.00"
        self.chart_container.content = None
        self.data_table_container.content = ft.Text("Genera la proyección para ver el detalle.", color=ft.colors.GREY_500)
        self.dict_resultados = {}
        self.update()

    def cambiar_modo(self, e):
        self.modo_actual = "semana" if self.tabs.selected_index == 0 else "mes"
        self.renderizar_resultados()
        
    def actualizar_datos(self, e):
        try:
            fd = None
            if self.fecha_desde.value:
                fd = datetime.datetime.strptime(self.fecha_desde.value, '%d/%m/%y').strftime('%Y%m%d')
                
            fh = None
            if self.fecha_hasta.value:
                fh = datetime.datetime.strptime(self.fecha_hasta.value, '%d/%m/%y').strftime('%Y%m%d')
        except ValueError:
            return
            
        self.dict_resultados = self.use_case.execute(fd, fh)
        self.renderizar_resultados()

    def renderizar_resultados(self):
        if not self.dict_resultados:
            return
            
        df_detalle = self.dict_resultados.get('detalle', pd.DataFrame())
        
        if df_detalle.empty:
            self.txt_total_cartera.value = "$ 0.00"
            self.chart_container.content = ft.Text("No se encontraron cheques en este rango de fechas.")
            self.data_table_container.content = ft.Text("")
            self.update()
            return
            
        total_importe = df_detalle['Importe'].sum()
        self.txt_total_cartera.value = f"${total_importe:,.2f}"
        
        if self.modo_actual == "semana":
            df_agrupado = self.dict_resultados['agrupado_semana']
            col_label = 'Semana_str'
            col_titulo = "Semana (Inicio)"
        else:
            df_agrupado = self.dict_resultados['agrupado_mes']
            col_label = 'Mes_str'
            col_titulo = "Mes"
            
        if df_agrupado.empty:
            return
            
        # Generar Gráfico
        chart_data = []
        max_y = df_agrupado['Importe'].max()
        
        labels = []
        for i, row in df_agrupado.iterrows():
            chart_data.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0, 
                            to_y=row['Importe'], 
                            width=30, 
                            color=ft.colors.BLUE_400, 
                            tooltip=f"{row[col_label]}\nImporte: ${row['Importe']:,.2f}"
                        )
                    ]
                )
            )
            labels.append(ft.ChartAxisLabel(value=i, label=ft.Text(row[col_label], size=10)))
            
        self.chart_container.content = ft.BarChart(
            bar_groups=chart_data,
            bottom_axis=ft.ChartAxis(labels=labels),
            max_y=max_y * 1.1,
            tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.GREY_300)
        )
        
        # Generar Tabla
        rows = []
        for _, row in df_agrupado.iterrows():
            periodo = row[col_label]
            importe = row['Importe']
            
            # Fila clickeable
            r = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(periodo, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(f"${importe:,.2f}"))
                ],
                on_select_changed=lambda e, p=periodo: self.mostrar_detalle(e, p)
            )
            rows.append(r)
            
        self.data_table_container.content = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(col_titulo)),
                ft.DataColumn(ft.Text("Total Importe ($)"), numeric=True)
            ],
            rows=rows,
            show_checkbox_column=False
        )
        
        self.update()

    def mostrar_detalle(self, e, periodo_str):
        df_detalle = self.dict_resultados.get('detalle', pd.DataFrame())
        if df_detalle.empty: return
        
        col_filtro = 'Semana_str' if self.modo_actual == "semana" else 'Mes_str'
        df_filtro = df_detalle[df_detalle[col_filtro] == periodo_str]
        
        # Ordenar los cheques por fecha de cheque
        df_filtro = df_filtro.sort_values(by='FechaCheque')
        
        rows = []
        for _, row in df_filtro.iterrows():
            n_interno = f"{row['NumeroInterno']:.0f}" if pd.notna(row['NumeroInterno']) else ""
            n_cheque = f"{row['NumeroCheque']:.0f}" if pd.notna(row['NumeroCheque']) else ""
            
            cliente = row['Cliente']
            razon_social = row['RazonSocial'] if 'RazonSocial' in row and pd.notna(row['RazonSocial']) else ""
            texto_cliente = f"{cliente} - {razon_social}" if razon_social else str(cliente)
            
            fecha = row['FechaCheque'].strftime('%d/%m/%Y')
            importe = row['Importe']
            
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(n_interno)),
                ft.DataCell(ft.Text(n_cheque)),
                ft.DataCell(ft.Text(texto_cliente)),
                ft.DataCell(ft.Text(fecha)),
                ft.DataCell(ft.Text(f"${importe:,.2f}"))
            ]))
            
        dlg = ft.AlertDialog(
            title=ft.Text(f"Detalle de Cheques - {periodo_str}"),
            content=ft.Column([
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Nº Interno")),
                        ft.DataColumn(ft.Text("Nº Cheque")),
                        ft.DataColumn(ft.Text("Cliente")),
                        ft.DataColumn(ft.Text("Fecha")),
                        ft.DataColumn(ft.Text("Importe ($)"), numeric=True)
                    ],
                    rows=rows
                )
            ], scroll=ft.ScrollMode.AUTO, height=400),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self.cerrar_dialog(dlg))]
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def cerrar_dialog(self, dlg):
        dlg.open = False
        self.page.update()
