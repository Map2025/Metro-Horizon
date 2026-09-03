import flet as ft
import datetime
from app.utils.export_utils import exportar_a_excel

class RatioVentasView(ft.Container):
    def __init__(self, use_case):
        super().__init__()
        self.use_case = use_case
        self.expand = True
        self.current_data = None
        
        # Date Pickers
        self.date_picker_desde = ft.DatePicker(
            on_change=lambda e: self.cambio_fecha(e, self.fecha_desde)
        )
        self.date_picker_hasta = ft.DatePicker(
            on_change=lambda e: self.cambio_fecha(e, self.fecha_hasta)
        )
        
        # Filtros UI
        self.fecha_desde = ft.TextField(label="Desde (DD/MM/AA)", value="01/01/26", width=150, read_only=True)
        self.btn_cal_desde = ft.IconButton(icon=ft.icons.CALENDAR_MONTH, on_click=lambda e: self.date_picker_desde.pick_date())
        
        self.fecha_hasta = ft.TextField(label="Hasta (DD/MM/AA)", value="31/12/26", width=150, read_only=True)
        self.btn_cal_hasta = ft.IconButton(icon=ft.icons.CALENDAR_MONTH, on_click=lambda e: self.date_picker_hasta.pick_date())
        
        self.btn_filtrar = ft.ElevatedButton("Generar Reporte", on_click=self.actualizar_datos, icon=ft.icons.SEARCH)
        self.btn_limpiar = ft.OutlinedButton("Limpiar", on_click=self.limpiar_datos, icon=ft.icons.CLEAR)
        self.btn_exportar = ft.OutlinedButton("Exportar a Excel", on_click=self.exportar, icon=ft.icons.TABLE_VIEW, icon_color=ft.colors.GREEN)

        # Contenedores dinámicos
        self.chart_container = ft.Container(height=300, padding=20)
        self.leyenda_container = ft.Container()
        self.tabla_container = ft.Container(expand=True)
        
        self.build_ui()

    def build_ui(self):
        self.content = ft.Column([
            ft.Text("Ratio de Ventas vs Cobranzas", size=24, weight="bold"),
            ft.Row([
                self.fecha_desde, self.btn_cal_desde,
                self.fecha_hasta, self.btn_cal_hasta,
                self.btn_filtrar, self.btn_limpiar, self.btn_exportar
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Divider(),
            self.leyenda_container,
            self.chart_container,
            ft.Divider(),
            self.tabla_container
        ], expand=True)
        
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
        self.current_data = None
        self.chart_container.content = None
        self.leyenda_container.content = None
        self.tabla_container.content = ft.Text("Genera el reporte para ver el detalle.", color=ft.colors.GREY_500)
        self.update()

    def exportar(self, e):
        exportar_a_excel(self.page, self.current_data, "Ratio_Ventas")

    def actualizar_datos(self, e):
        try:
            fd = datetime.datetime.strptime(self.fecha_desde.value, '%d/%m/%y').strftime('%Y-%m-%d')
            fh = datetime.datetime.strptime(self.fecha_hasta.value, '%d/%m/%y').strftime('%Y-%m-%d')
        except ValueError:
            return
            
        data = self.use_case.execute(fd, fh)
        self.current_data = data
        
        if not data:
            self.chart_container.content = None
            self.leyenda_container.content = None
            self.tabla_container.content = ft.Text("No hay datos suficientes para el periodo seleccionado.", color="red")
            self.update()
            return

        chart_groups = []
        labels = []
        
        for i, row in enumerate(data):
            labels.append(ft.ChartAxisLabel(value=i, label=ft.Text(row['Periodo'], size=10)))
            
            chart_groups.append(ft.BarChartGroup(
                x=i,
                bar_rods=[
                    ft.BarChartRod(
                        from_y=0, 
                        to_y=row['TotalVentas'], 
                        color=ft.colors.BLUE_400, 
                        width=15, 
                        tooltip=f"Ventas: ${row['TotalVentas']:,.2f}"
                    ),
                    ft.BarChartRod(
                        from_y=0, 
                        to_y=row['TotalCobrado'], 
                        color=ft.colors.GREEN_400, 
                        width=15, 
                        tooltip=f"Cobranzas: ${row['TotalCobrado']:,.2f}"
                    )
                ],
            ))

        self.chart_container.content = ft.BarChart(
            bar_groups=chart_groups,
            border=ft.border.all(1, ft.colors.OUTLINE),
            left_axis=ft.ChartAxis(labels_size=50),
            bottom_axis=ft.ChartAxis(labels=labels, labels_size=30),
            expand=True
        )

        self.leyenda_container.content = ft.Row([
            ft.Container(width=15, height=15, bgcolor=ft.colors.BLUE_400), ft.Text("Facturado"),
            ft.Container(width=20),
            ft.Container(width=15, height=15, bgcolor=ft.colors.GREEN_400), ft.Text("Cobrado"),
        ], alignment=ft.MainAxisAlignment.CENTER)

        rows = []
        for row in data:
            color = "green" if row['Ratio (%)'] >= 90 else "orange" if row['Ratio (%)'] >= 70 else "red"
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(row['Periodo'])),
                ft.DataCell(ft.Text(f"${row['TotalVentas']:,.2f}")),
                ft.DataCell(ft.Text(f"${row['TotalCobrado']:,.2f}")),
                ft.DataCell(ft.Text(f"{row['Ratio (%)']}%", color=color, weight="bold")),
            ]))
            
        tabla = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Periodo")), 
                ft.DataColumn(ft.Text("Total Facturado (incluye IVA)", text_align="right")), 
                ft.DataColumn(ft.Text("Total Cobrado", text_align="right")), 
                ft.DataColumn(ft.Text("Ratio Eficiencia", text_align="right"))
            ], 
            rows=rows, expand=True
        )
        self.tabla_container.content = ft.ListView([tabla], expand=True)

        self.update()
