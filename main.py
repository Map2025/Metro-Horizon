import flet as ft
import os
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

# Cargar variables de entorno desde el archivo .env
load_dotenv()

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
        
    repository_morosidad = MorosidadRepository(CONNECTION_STRING)
    ml_service = MorosidadService()
    use_case_morosidad = GetRiesgoMorosidadUseCase(repository_morosidad, ml_service)
    
    repository_cf = CashFlowRepository(CONNECTION_STRING)
    use_case_cf = GetProyeccionCashFlowUseCase(repository_cf, repository_morosidad, ml_service)
    
    repository_flujo_real = FlujoRealRepository(CONNECTION_STRING)
    use_case_flujo_real = GetFlujoRealUseCase(repository_flujo_real)

    repository_ventas = VentasRepository(CONNECTION_STRING)
    use_case_ventas = GetRatioVentasUseCase(repository_ventas)

    # Vistas
    morosidad_view = MorosidadView(use_case_morosidad)
    cashflow_view = CashFlowView(use_case_cf)
    vista_flujo_real = FlujoRealView(use_case_flujo_real)
    vista_ventas = RatioVentasView(use_case_ventas)

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
        
        # Ignorar clics en los títulos (índices 0 y 3)
        if index == 0 or index == 3:
            # Revertir selección al anterior
            e.control.selected_index = last_selected_index
            page.update()
            return
            
        last_selected_index = index
        
        if index == 1:
            content_area.content = vista_flujo_real
        elif index == 2:
            content_area.content = vista_ventas
        elif index == 4:
            content_area.content = cashflow_view
        elif index == 5:
            content_area.content = morosidad_view
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
                icon=ft.icons.BATCH_PREDICTION, label="--- PREDICTIVOS ---"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.TRENDING_UP, selected_icon=ft.icons.TRENDING_UP_OUTLINED, label="Cash Flow"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.WARNING, selected_icon=ft.icons.WARNING_OUTLINED, label="Riesgo Morosidad"
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
