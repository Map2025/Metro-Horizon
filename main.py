import flet as ft
import os
import sys
import pyodbc
from dotenv import load_dotenv
from app.data.repositories.morosidad_repository import MorosidadRepository
from app.ml.services.morosidad_service import MorosidadService
from app.domain.use_cases.get_riesgo_morosidad import GetRiesgoMorosidadUseCase
from app.ui.views.morosidad_view import MorosidadView

from app.data.repositories.cashflow_repository import CashFlowRepository
from app.domain.use_cases.get_proyeccion_cashflow import GetProyeccionCashFlowUseCase
from app.ui.views.cashflow_view import CashFlowView

from app.data.repositories.flujo_real_repository import FlujoRealRepository
from app.domain.use_cases.get_flujo_real_use_case import GetFlujoRealUseCase
from app.ui.views.flujo_real_view import FlujoRealView

from app.data.repositories.ventas_repository import VentasRepository
from app.domain.use_cases.get_ratio_ventas_use_case import GetRatioVentasUseCase
from app.ui.views.ratio_ventas_view import RatioVentasView
from app.ui.views.acerca_de_view import AcercaDeView

from app.data.repositories.cheques_repository import ChequesRepository
from app.domain.use_cases.get_proyeccion_cheques_use_case import GetProyeccionChequesUseCase
from app.ui.views.proyeccion_cheques_view import ProyeccionChequesView

from app.data.repositories.ciclo_cheques_repository import CicloChequesRepository
from app.domain.use_cases.ciclo_cheques_service import ChequeAnalyticsService
from app.ui.views.ciclo_cheques_view import CicloChequesView


# Lógica robusta para encontrar el archivo .env incluso estando compilado como .exe
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(application_path, '.env')
load_dotenv(dotenv_path=env_path)

def main(page: ft.Page):
    page.title = "Metro Horizon"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20

    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            theme_btn.icon = ft.icons.LIGHT_MODE
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_btn.icon = ft.icons.DARK_MODE
        page.update()

    theme_btn = ft.IconButton(
        icon=ft.icons.DARK_MODE,
        on_click=toggle_theme,
        tooltip="Cambiar tema (Claro/Oscuro)"
    )

    page.appbar = ft.AppBar(
        title=ft.Text("Dashboard Principal"),
        center_title=False,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[theme_btn, ft.Container(width=10)]
    )

    # Inicializar Arquitectura (Inyección de Dependencias)
    CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")
    if not CONNECTION_STRING:
        # Fallback de seguridad en caso de que no exista el .env
        CONNECTION_STRING = "Driver={SQL Server};Server=localhost;Database=SISAT_SOLUCIONES__SA;Trusted_Connection=yes;"
    
    # Extraer base de datos actual para el dropdown
    current_db = ""
    for p in CONNECTION_STRING.split(';'):
        if p.strip().lower().startswith('database='):
            current_db = p.split('=')[1].strip()

    # NUEVO: Prueba de conexión al arrancar y obtención de bases de datos
    databases = []
    try:
        conn = pyodbc.connect(CONNECTION_STRING, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.databases WHERE state = 0 AND name NOT IN ('master', 'tempdb', 'model', 'msdb')")
        databases = [row[0] for row in cursor.fetchall()]
        conn.close()
    except Exception as ex:
        # Mostramos un cartel rojo gigante en la pantalla del usuario si falla la conexión
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"ERROR DE CONEXIÓN A BASE DE DATOS:\n{str(ex)}"),
            bgcolor=ft.colors.RED_900,
            duration=15000,
            action="OK"
        )
        page.snack_bar.open = True
        
    if current_db and current_db not in databases:
        databases.append(current_db)
        
    repository_morosidad = MorosidadRepository(CONNECTION_STRING)
    ml_service = MorosidadService()
    use_case_morosidad = GetRiesgoMorosidadUseCase(repository_morosidad, ml_service)
    
    repository_cf = CashFlowRepository(CONNECTION_STRING)
    use_case_cf = GetProyeccionCashFlowUseCase(repository_cf, repository_morosidad, ml_service)
    
    repository_flujo_real = FlujoRealRepository(CONNECTION_STRING)
    use_case_flujo_real = GetFlujoRealUseCase(repository_flujo_real)

    repository_ventas = VentasRepository(CONNECTION_STRING)
    use_case_ventas = GetRatioVentasUseCase(repository_ventas)
    
    repository_cheques = ChequesRepository(CONNECTION_STRING)
    use_case_cheques = GetProyeccionChequesUseCase(repository_cheques)

    repository_ciclo_cheques = CicloChequesRepository(CONNECTION_STRING)
    use_case_ciclo_cheques = ChequeAnalyticsService(repository_ciclo_cheques)
    
    def on_db_change(e):
        new_db = e.control.value
        parts = CONNECTION_STRING.split(';')
        for i, p in enumerate(parts):
            if p.strip().lower().startswith('database='):
                parts[i] = f'Database={new_db}'
        new_conn_str = ';'.join(parts)
        
        repository_morosidad.connection_string = new_conn_str
        repository_cf.connection_string = new_conn_str
        repository_flujo_real.connection_string = new_conn_str
        repository_ventas.connection_string = new_conn_str
        repository_cheques.connection_string = new_conn_str
        repository_ciclo_cheques.connection_string = new_conn_str
        
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Base de datos cambiada a {new_db}. Genere el reporte nuevamente."), 
            bgcolor=ft.colors.GREEN_700
        )
        page.snack_bar.open = True
        page.update()

    db_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(db) for db in databases],
        value=current_db,
        width=250,
        on_change=on_db_change,
        dense=True,
        text_size=14,
        disabled=len(databases) <= 1
    )
    
    # Agregar el dropdown al AppBar
    page.appbar.actions.insert(0, db_dropdown)
    page.appbar.actions.insert(1, ft.Container(width=20))


    # Vistas
    morosidad_view = MorosidadView(use_case_morosidad)
    cashflow_view = CashFlowView(use_case_cf)
    vista_flujo_real = FlujoRealView(use_case_flujo_real)
    vista_ventas = RatioVentasView(use_case_ventas)
    vista_cheques = ProyeccionChequesView(use_case_cheques)
    vista_ciclo_cheques = CicloChequesView(use_case_ciclo_cheques)
    vista_acerca_de = AcercaDeView()

    # Variables de estado
    last_selected_index = 1

    # Contenedor principal de contenido
    content_area = ft.Container(
        content=vista_flujo_real,
        expand=True,
        padding=20,
    )

    def on_nav_change(e):
        nonlocal last_selected_index
        index = e.control.selected_index
        
        # Ignorar clics en los títulos (índices 0, 5 y 8)
        if index == 0 or index == 5 or index == 8:
            # Revertir selección al anterior
            e.control.selected_index = last_selected_index
            page.update()
            return
            
        last_selected_index = index
        
        if index == 1:
            content_area.content = vista_flujo_real
        elif index == 2:
            content_area.content = vista_ventas
        elif index == 3:
            content_area.content = vista_cheques
        elif index == 4:
            content_area.content = vista_ciclo_cheques
        elif index == 6:
            content_area.content = cashflow_view
        elif index == 7:
            content_area.content = morosidad_view
        elif index == 9:
            content_area.content = vista_acerca_de
        page.update()

    # Menú lateral
    rail = ft.NavigationRail(
        selected_index=1,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.ANALYTICS, label="--- ANALÍTICOS ---"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.ATTACH_MONEY, selected_icon=ft.icons.ATTACH_MONEY_OUTLINED, label="Flujo Real"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.COMPARE_ARROWS, selected_icon=ft.icons.COMPARE_ARROWS_OUTLINED, label="Ratio Cobranzas"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.ACCOUNT_BALANCE_WALLET, selected_icon=ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, label="Cartera Cheques"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.TIMELAPSE, selected_icon=ft.icons.TIMELAPSE_OUTLINED, label="Ciclo Cheques"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.BATCH_PREDICTION, label="--- PREDICTIVOS ---"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.TRENDING_UP, selected_icon=ft.icons.TRENDING_UP_OUTLINED, label="Cash Flow"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.WARNING, selected_icon=ft.icons.WARNING_OUTLINED, label="Riesgo Morosidad"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.INFO, label="--- SISTEMA ---"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.HELP_OUTLINE, selected_icon=ft.icons.HELP, label="Acerca de"
            ),
        ],
        on_change=on_nav_change,
    )

    page.add(
        ft.Row(
            [
                rail,
                ft.VerticalDivider(width=1),
                content_area,
            ],
            expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
