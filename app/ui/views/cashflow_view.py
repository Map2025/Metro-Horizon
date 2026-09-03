import flet as ft
from app.domain.use_cases.get_proyeccion_cashflow import GetProyeccionCashFlowUseCase
import flet.canvas as cv
import pandas as pd
from app.utils.export_utils import exportar_a_excel

class CashFlowView(ft.Container):
    def __init__(self, use_case: GetProyeccionCashFlowUseCase):
        super().__init__()
        self.use_case = use_case
        self.expand = True
        self.dict_resultados = {}
        
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Período")),
                ft.DataColumn(ft.Text("Ingresos Estimados ($)"), numeric=True),
                ft.DataColumn(ft.Text("Egresos Estimados ($)"), numeric=True),
                ft.DataColumn(ft.Text("Saldo Acumulado ($)"), numeric=True),
            ],
            rows=[]
        )
        
        self.chart_container = ft.Container(height=300, padding=20)
        self.btn_exportar = ft.OutlinedButton("Exportar a Excel", on_click=self.exportar, icon=ft.icons.TABLE_VIEW, icon_color=ft.colors.GREEN)

        self.content = ft.Column([
            ft.Text("Proyección de Flujo de Caja (Cash Flow)", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Haz clic sobre el monto de los Ingresos para ver el detalle de composición.", color=ft.colors.GREY_500),
            ft.Divider(),
            ft.Row([
                ft.ElevatedButton("Generar Proyección", on_click=self.actualizar_datos),
                self.btn_exportar
            ]),
            self.chart_container,
            ft.Divider(),
            self.data_table
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def exportar(self, e):
        df_export = self.dict_resultados.get('flujo')
        if df_export is not None:
            exportar_a_excel(self.page, df_export, "Proyeccion_CashFlow")

    def mostrar_detalle(self, e, periodo, columna_detalle):
        if not self.dict_resultados:
            return
            
        cheques_terceros = self.dict_resultados.get('cheques_terceros', 0)
        df_clientes = self.dict_resultados.get('clientes_detalle', pd.DataFrame())
        
        if periodo == 'Hoy (Liquidez Inicial)':
            content_body = ft.Text(f"Los ingresos iniciales corresponden a los cheques de terceros al día (vencidos o con vencimiento hoy) por un monto de ${cheques_terceros:,.2f}")
        else:
            rows_clientes = []
            # Filtrar clientes que realmente van a pagar esta semana y mostrarlos ordenados
            df_semana = df_clientes[df_clientes[columna_detalle] > 0].sort_values(by=columna_detalle, ascending=False).head(20)
            
            for _, c in df_semana.iterrows():
                monto_semana = c[columna_detalle]
                rows_clientes.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(c.get('RazonSocial', '')))),
                        ft.DataCell(ft.Text(f"${monto_semana:,.2f}"))
                    ])
                )
            
            total_cobranzas = df_clientes[columna_detalle].sum() if not df_clientes.empty and columna_detalle in df_clientes else 0
            
            # Buscar cheques que vencen en esta semana
            rows_cheques = []
            total_cheques = 0
            df_cheques_terceros = self.dict_resultados.get('df_cheques_terceros', pd.DataFrame())
            if not df_cheques_terceros.empty:
                try:
                    semana_idx = int(periodo.split(' ')[1]) - 1
                    hoy = pd.Timestamp.today().normalize()
                    fecha_inicio = hoy + pd.Timedelta(days=semana_idx*7)
                    fecha_fin = hoy + pd.Timedelta(days=(semana_idx+1)*7)
                    
                    mask = (df_cheques_terceros['FechaVencimiento'] > fecha_inicio) & (df_cheques_terceros['FechaVencimiento'] <= fecha_fin)
                    cheques_semana = df_cheques_terceros[mask]
                    total_cheques = cheques_semana['Importe'].sum()
                    
                    for _, ch in cheques_semana.iterrows():
                        fecha_str = ch['FechaVencimiento'].strftime('%d/%m/%y')
                        rows_cheques.append(
                            ft.DataRow(cells=[
                                ft.DataCell(ft.Text(f"Cheque Venc: {fecha_str}")),
                                ft.DataCell(ft.Text(f"${ch['Importe']:,.2f}"))
                            ])
                        )
                except Exception:
                    pass
            
            elementos_columna = [
                ft.Text(f"Composición de Cobros ({periodo})", weight=ft.FontWeight.BOLD),
                ft.Text(f"Cobranza de Clientes (Ajustado por ML) - Total: ${total_cobranzas:,.2f}", color=ft.colors.BLUE_700, weight=ft.FontWeight.W_500),
                ft.DataTable(
                    columns=[ft.DataColumn(ft.Text("Cliente")), ft.DataColumn(ft.Text("Ingreso Esperado ($)"), numeric=True)],
                    rows=rows_clientes
                )
            ]
            
            if rows_cheques or total_cheques > 0:
                elementos_columna.extend([
                    ft.Divider(),
                    ft.Text(f"Cheques de Terceros a cobrar - Total: ${total_cheques:,.2f}", color=ft.colors.GREEN_700, weight=ft.FontWeight.W_500),
                    ft.DataTable(
                        columns=[ft.DataColumn(ft.Text("Cheque")), ft.DataColumn(ft.Text("Importe ($)"), numeric=True)],
                        rows=rows_cheques
                    )
                ])
                
            content_body = ft.Column(elementos_columna, scroll=ft.ScrollMode.AUTO, height=350)
            
        dlg = ft.AlertDialog(
            title=ft.Text(f"Detalle: {periodo}"),
            content=content_body,
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self.cerrar_dialog(dlg))]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def cerrar_dialog(self, dlg):
        dlg.open = False
        self.page.update()

    def actualizar_datos(self, e):
        self.dict_resultados = self.use_case.execute()
        df_resultados = self.dict_resultados['flujo']
        
        self.data_table.rows.clear()
        
        chart_data = []
        max_y = 0
        min_y = 0
        
        for index, row in df_resultados.iterrows():
            saldo_color = ft.colors.RED_500 if row['Saldo Acumulado'] < 0 else ft.colors.GREEN_500
            
            # Celda Clickable para Ingresos
            ingresos_cell = ft.DataCell(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(f"{row['Ingresos']:,.2f}", color=ft.colors.BLUE_600, weight=ft.FontWeight.W_500),
                            ft.Icon(ft.icons.SEARCH, size=16, color=ft.colors.BLUE_600)
                        ],
                        alignment=ft.MainAxisAlignment.END
                    ),
                    on_click=lambda e, p=row['Periodo'], col=row['ColumnaDetalle']: self.mostrar_detalle(e, p, col),
                    tooltip="Ver composición"
                )
            )
            
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(row['Periodo'], weight=ft.FontWeight.BOLD)),
                        ingresos_cell,
                        ft.DataCell(ft.Text(f"{row['Egresos']:,.2f}")),
                        ft.DataCell(ft.Text(f"{row['Saldo Acumulado']:,.2f}", color=saldo_color, weight=ft.FontWeight.BOLD)),
                    ]
                )
            )
            
            val = float(row['Saldo Acumulado'])
            if val > max_y: max_y = val
            if val < min_y: min_y = val
            
            chart_data.append(
                ft.BarChartGroup(
                    x=index,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=val,
                            width=40,
                            color=ft.colors.RED_400 if val < 0 else ft.colors.BLUE_400,
                            tooltip=f"{row['Periodo']}: ${val:,.2f}",
                            border_radius=0,
                        ),
                    ],
                )
            )

        rango = max(abs(max_y), abs(min_y))
        if rango == 0: rango = 1000 
        
        chart = ft.BarChart(
            bar_groups=chart_data,
            border=ft.border.all(1, ft.colors.GREY_400),
            left_axis=ft.ChartAxis(
                labels_size=40, title=ft.Text("Saldo Acumulado"), title_size=40
            ),
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(
                        value=i, label=ft.Container(ft.Text(df_resultados.iloc[i]['Periodo'][:8]), padding=10)
                    )
                    for i in range(len(df_resultados))
                ],
                labels_size=40,
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.colors.GREY_300, width=1, dash_pattern=[3, 3]
            ),
            tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.GREY_300),
            max_y=max_y + (rango * 0.1),
            min_y=min_y - (rango * 0.1) if min_y < 0 else 0,
            expand=True,
        )
        
        self.chart_container.content = chart
        self.update()
