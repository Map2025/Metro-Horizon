import flet as ft
from app.domain.use_cases.get_riesgo_morosidad import GetRiesgoMorosidadUseCase
import pandas as pd
from app.utils.export_utils import exportar_a_excel

class MorosidadView(ft.Container):
    def __init__(self, use_case: GetRiesgoMorosidadUseCase):
        super().__init__()
        self.use_case = use_case
        self.expand = True
        self.df_resultados = pd.DataFrame()
        
        self.filtro_riesgo = ft.Dropdown(
            label="Filtrar por Riesgo",
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("Alto"),
                ft.dropdown.Option("Medio"),
                ft.dropdown.Option("Bajo"),
            ],
            value="Todos",
            on_change=self.aplicar_filtro,
            width=200
        )
        
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código Cliente")),
                ft.DataColumn(ft.Text("Razón Social")),
                ft.DataColumn(ft.Text("Saldo Actual ($)"), numeric=True),
                ft.DataColumn(ft.Text("Última Factura")),
                ft.DataColumn(ft.Text("Último Recibo")),
                ft.DataColumn(ft.Text("Score Riesgo (%)"), numeric=True),
                ft.DataColumn(ft.Text("Nivel Riesgo")),
            ],
            rows=[]
        )

        self.btn_exportar = ft.OutlinedButton("Exportar a Excel", on_click=self.exportar, icon=ft.icons.TABLE_VIEW, icon_color=ft.colors.GREEN)

        self.content = ft.Column([
            ft.Text("Riesgo de Morosidad por Cliente", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row([
                ft.Row([
                    ft.ElevatedButton("Calcular Riesgo / Actualizar Datos", on_click=self.actualizar_datos),
                    self.btn_exportar
                ]),
                self.filtro_riesgo
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.data_table
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def exportar(self, e):
        exportar_a_excel(self.page, self.df_resultados, "Riesgo_Morosidad")

    def actualizar_datos(self, e):
        self.df_resultados = self.use_case.execute()
        self.renderizar_tabla()

    def aplicar_filtro(self, e):
        self.renderizar_tabla()

    def renderizar_tabla(self):
        if self.df_resultados.empty:
            return
            
        filtro = self.filtro_riesgo.value
        if filtro != "Todos":
            df_mostrar = self.df_resultados[self.df_resultados['Nivel_Riesgo'] == filtro]
        else:
            df_mostrar = self.df_resultados
            
        self.data_table.rows.clear()
        
        for _, row in df_mostrar.iterrows():
            
            # Color basado en el nivel de riesgo
            color = None
            if row['Nivel_Riesgo'] == 'Alto':
                color = ft.colors.RED_500 if self.page and self.page.theme_mode == ft.ThemeMode.DARK else ft.colors.RED_700
            elif row['Nivel_Riesgo'] == 'Medio':
                color = ft.colors.ORANGE_500 if self.page and self.page.theme_mode == ft.ThemeMode.DARK else ft.colors.ORANGE_700
            elif row['Nivel_Riesgo'] == 'Bajo':
                color = ft.colors.GREEN_500 if self.page and self.page.theme_mode == ft.ThemeMode.DARK else ft.colors.GREEN_700
                
            # Formatear fechas a DD/MM/AA
            str_fecha_factura = pd.to_datetime(row['FechaUltimaFactura']).strftime('%d/%m/%y') if pd.notnull(row['FechaUltimaFactura']) else 'Sin facturas'
            str_fecha_recibo = pd.to_datetime(row['FechaUltimoRecibo']).strftime('%d/%m/%y') if pd.notnull(row['FechaUltimoRecibo']) else 'Sin pagos'
                
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row['CodigoCliente']))),
                        ft.DataCell(ft.Text(str(row['RazonSocial']))),
                        ft.DataCell(ft.Text(f"{row['SaldoActual']:,.2f}")),
                        ft.DataCell(ft.Text(str_fecha_factura)),
                        ft.DataCell(ft.Text(str_fecha_recibo)),
                        ft.DataCell(ft.Text(f"{row['Score_Riesgo']:.2f}", color=color, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(str(row['Nivel_Riesgo']), color=color, weight=ft.FontWeight.BOLD)),
                    ]
                )
            )
        self.update()
