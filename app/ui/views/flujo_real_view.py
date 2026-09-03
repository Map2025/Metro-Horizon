import flet as ft
from app.domain.use_cases.get_flujo_real_use_case import GetFlujoRealUseCase
import pandas as pd
import datetime
from app.utils.export_utils import exportar_a_excel

class FlujoRealView(ft.Container):
    def __init__(self, use_case: GetFlujoRealUseCase):
        super().__init__()
        self.use_case = use_case
        self.expand = True
        self.dict_resultados = {}
        
        # Date Pickers
        self.date_picker_desde = ft.DatePicker(
            on_change=lambda e: self.cambio_fecha(e, self.fecha_desde)
        )
        self.date_picker_hasta = ft.DatePicker(
            on_change=lambda e: self.cambio_fecha(e, self.fecha_hasta)
        )
        
        # Filtros
        self.fecha_desde = ft.TextField(label="Desde (DD/MM/AA)", value="01/07/26", width=150, read_only=True)
        self.btn_cal_desde = ft.IconButton(icon=ft.icons.CALENDAR_MONTH, on_click=lambda e: self.date_picker_desde.pick_date())
        
        self.fecha_hasta = ft.TextField(label="Hasta (DD/MM/AA)", value="31/07/26", width=150, read_only=True)
        self.btn_cal_hasta = ft.IconButton(icon=ft.icons.CALENDAR_MONTH, on_click=lambda e: self.date_picker_hasta.pick_date())
        
        self.btn_generar = ft.ElevatedButton("Generar Flujo Real", on_click=self.actualizar_datos, icon=ft.icons.PLAY_ARROW)
        self.btn_limpiar = ft.OutlinedButton("Limpiar", on_click=self.limpiar_datos, icon=ft.icons.CLEAR)
        self.btn_exportar = ft.OutlinedButton("Exportar a Excel", on_click=self.exportar, icon=ft.icons.TABLE_VIEW, icon_color=ft.colors.GREEN)
        
        # KPIs
        self.txt_ingresos = ft.Text("$ 0.00", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700)
        self.txt_egresos = ft.Text("$ 0.00", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.RED_700)
        self.txt_saldo_final = ft.Text("$ 0.00", size=20, weight=ft.FontWeight.BOLD)
        
        def create_kpi_card(title, text_control):
            return ft.Card(
                content=ft.Container(
                    content=ft.Column([ft.Text(title, size=14, color=ft.colors.GREY_700), text_control]),
                    padding=20,
                    width=200
                )
            )
            
        self.kpi_row = ft.Row([
            create_kpi_card("Total Ingresos", self.txt_ingresos),
            create_kpi_card("Total Egresos", self.txt_egresos),
            create_kpi_card("Saldo Final (Flujo Neto)", self.txt_saldo_final)
        ])
        
        self.chart_container = ft.Container(height=300, expand=2)
        self.pie_container = ft.Container(height=300, expand=1)
        self.data_table_container = ft.Container(content=ft.Text("Genera el reporte para ver el detalle.", color=ft.colors.GREY_500))
        self.resumen_cuentas_container = ft.Container()
        
        self.content = ft.Column([
            ft.Text("Flujo de Efectivo Real (Tesorería)", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([
                self.fecha_desde, self.btn_cal_desde,
                self.fecha_hasta, self.btn_cal_hasta, 
                self.btn_generar, self.btn_limpiar, self.btn_exportar
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Divider(),
            self.kpi_row,
            ft.Row([self.chart_container, self.pie_container]),
            ft.Divider(),
            ft.Text("Resumen por Cuenta", size=18, weight=ft.FontWeight.BOLD),
            self.resumen_cuentas_container,
            ft.Divider(),
            ft.Text("Detalle del Flujo Neto", size=18, weight=ft.FontWeight.BOLD),
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
        self.txt_ingresos.value = "$ 0.00"
        self.txt_egresos.value = "$ 0.00"
        self.txt_saldo_final.value = "$ 0.00"
        self.chart_container.content = None
        self.pie_container.content = None
        self.resumen_cuentas_container.content = None
        self.data_table_container.content = ft.Text("Genera el reporte para ver el detalle.", color=ft.colors.GREY_500)
        self.update()

    def exportar(self, e):
        df_export = self.dict_resultados.get('detalle_movimientos')
        if df_export is not None:
            exportar_a_excel(self.page, df_export, "Flujo_Efectivo_Real")
        else:
            exportar_a_excel(self.page, None, "Flujo_Efectivo_Real")

    def mostrar_detalle(self, e, concepto, tipo):
        df_detalle = self.dict_resultados.get('detalle_movimientos', pd.DataFrame())
        if df_detalle.empty: return
        
        df_filtro = df_detalle[(df_detalle['DESCRIPCIO'] == concepto) & (df_detalle['TIPO'] == tipo)]
        
        rows = []
        for _, row in df_filtro.iterrows():
            monto = abs(row['MONTO'])
            fecha_str = row['FECHA'].strftime('%d/%m/%y')
            
            razon_social = row.get('NOMBRE_PROVEEDOR') or row.get('NOMBRE_CLIENTE') or "-"
            if pd.isna(razon_social):
                razon_social = "-"
                
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(fecha_str)),
                ft.DataCell(ft.Text(str(row['N_COMP']))),
                ft.DataCell(ft.Text(str(razon_social))),
                ft.DataCell(ft.Text(f"${monto:,.2f}"))
            ]))
            
        dlg = ft.AlertDialog(
            title=ft.Text(f"Detalle de Movimientos: {concepto}"),
            content=ft.Column([
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Fecha")),
                        ft.DataColumn(ft.Text("Comprobante")),
                        ft.DataColumn(ft.Text("Razón Social")),
                        ft.DataColumn(ft.Text("Importe ($)"), numeric=True)
                    ],
                    rows=rows
                )
            ], scroll=ft.ScrollMode.AUTO, height=300),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self.cerrar_dialog(dlg))]
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def cerrar_dialog(self, dlg):
        dlg.open = False
        self.page.update()

    def actualizar_datos(self, e):
        try:
            fd = datetime.datetime.strptime(self.fecha_desde.value, '%d/%m/%y').strftime('%Y-%m-%d')
            fh = datetime.datetime.strptime(self.fecha_hasta.value, '%d/%m/%y').strftime('%Y-%m-%d')
        except ValueError:
            return
            
        self.dict_resultados = self.use_case.execute(fd, fh)
        
        df_kpi = self.dict_resultados['flujo_kpi']
        df_pivot = self.dict_resultados['pivot_conceptos']
        periodos = self.dict_resultados['periodos']
        df_resumen = self.dict_resultados.get('resumen_cuentas', pd.DataFrame())
        
        if df_kpi.empty:
            return
            
        tot_ing = df_kpi['Ingresos'].sum()
        tot_egr = df_kpi['Egresos'].sum()
        saldo_fin = tot_ing - tot_egr
        
        self.txt_ingresos.value = f"${tot_ing:,.2f}"
        self.txt_egresos.value = f"${tot_egr:,.2f}"
        self.txt_saldo_final.value = f"${saldo_fin:,.2f}"
        self.txt_saldo_final.color = ft.colors.GREEN_700 if saldo_fin >= 0 else ft.colors.RED_700

        if not df_resumen.empty:
            filas_resumen = []
            for _, r in df_resumen.iterrows():
                filas_resumen.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(r['Cuenta'])),
                    ft.DataCell(ft.Text(f"${r['Neto']:,.2f}"))
                ]))
            filas_resumen.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text("TOTAL", weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(f"${saldo_fin:,.2f}", weight=ft.FontWeight.BOLD))
            ]))
            
            self.resumen_cuentas_container.content = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Cuenta de Liquidez", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Flujo Neto ($)", weight=ft.FontWeight.BOLD), numeric=True)
                ],
                rows=filas_resumen
            )
        else:
            self.resumen_cuentas_container.content = ft.Text("No hay movimientos.", color=ft.colors.GREY_500)
        
        columns = [ft.DataColumn(ft.Text("Tipo")), ft.DataColumn(ft.Text("Concepto"))]
        for p in periodos:
            columns.append(ft.DataColumn(ft.Text(p), numeric=True))
        columns.append(ft.DataColumn(ft.Text("Total"), numeric=True))
        
        rows = []
        for _, row in df_pivot.iterrows():
            cells = [
                ft.DataCell(ft.Text(row['TIPO'], weight=ft.FontWeight.BOLD, color=ft.colors.GREEN if row['TIPO'] == 'Ingreso' else ft.colors.RED)),
                ft.DataCell(ft.Text(row['DESCRIPCIO']))
            ]
            total_fila = 0
            for p in periodos:
                val = abs(row.get(p, 0))
                total_fila += val
                cells.append(ft.DataCell(ft.Text(f"${val:,.2f}")))
                
            cells.append(ft.DataCell(ft.Text(f"${total_fila:,.2f}", weight=ft.FontWeight.BOLD)))
            
            r = ft.DataRow(cells=cells, on_select_changed=lambda e, c=row['DESCRIPCIO'], t=row['TIPO']: self.mostrar_detalle(e, c, t))
            rows.append(r)
            
        self.data_table_container.content = ft.DataTable(columns=columns, rows=rows, show_checkbox_column=False)
        
        chart_data = []
        max_y = 0
        for i, row in df_kpi.iterrows():
            if row['Ingresos'] > max_y: max_y = row['Ingresos']
            if row['Egresos'] > max_y: max_y = row['Egresos']
            
            chart_data.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(from_y=0, to_y=row['Ingresos'], width=20, color=ft.colors.BLUE_400, tooltip=f"Ingresos: ${row['Ingresos']:,.2f}"),
                        ft.BarChartRod(from_y=0, to_y=row['Egresos'], width=20, color=ft.colors.RED_400, tooltip=f"Egresos: ${row['Egresos']:,.2f}"),
                    ]
                )
            )
        
        self.chart_container.content = ft.BarChart(
            bar_groups=chart_data,
            bottom_axis=ft.ChartAxis(
                labels=[ft.ChartAxisLabel(value=i, label=ft.Text(df_kpi.iloc[i]['Periodo'])) for i in range(len(df_kpi))]
            ),
            max_y=max_y * 1.1,
            tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.GREY_300)
        )
        
        df_egresos = df_pivot[df_pivot['TIPO'] == 'Egreso'].copy()
        if not df_egresos.empty:
            df_egresos['TotalEgreso'] = df_egresos[periodos].sum(axis=1).abs()
            top_egresos = df_egresos.sort_values('TotalEgreso', ascending=False).head(5)
            
            colors = [ft.colors.RED_400, ft.colors.ORANGE_400, ft.colors.YELLOW_600, ft.colors.PINK_400, ft.colors.PURPLE_400]
            pie_sections = []
            for i, (_, r) in enumerate(top_egresos.iterrows()):
                c = colors[i % len(colors)]
                pie_sections.append(ft.PieChartSection(r['TotalEgreso'], title=r['DESCRIPCIO'][:10], color=c, radius=100))
                
            self.pie_container.content = ft.PieChart(sections=pie_sections, sections_space=2, center_space_radius=0)
        else:
            self.pie_container.content = ft.Text("No hay egresos para graficar")
            
        self.update()
