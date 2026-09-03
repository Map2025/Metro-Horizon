import pandas as pd
import flet as ft
from datetime import datetime
import os
from pathlib import Path

def exportar_a_excel(page: ft.Page, data, report_name: str):
    """
    Exporta datos (DataFrame o lista de diccionarios) a un archivo Excel.
    Guarda el archivo en la carpeta de Descargas del usuario.
    """
    if data is None or (isinstance(data, list) and len(data) == 0) or (isinstance(data, pd.DataFrame) and data.empty):
        page.snack_bar = ft.SnackBar(ft.Text("No hay datos para exportar."), bgcolor=ft.colors.RED_700)
        page.snack_bar.open = True
        page.update()
        return

    try:
        # Convertir a DataFrame si es una lista de diccionarios
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        downloads_path = str(Path.home() / "Downloads")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_name}_{timestamp}.xlsx"
        full_path = os.path.join(downloads_path, filename)
        
        df.to_excel(full_path, index=False)
        
        page.snack_bar = ft.SnackBar(
            ft.Text(f"Exportado exitosamente a:\n{full_path}"), 
            bgcolor=ft.colors.GREEN_700,
            duration=5000
        )
        page.snack_bar.open = True
        page.update()
        
        # Opcional: Intentar abrir en Windows
        if os.name == 'nt':
            os.startfile(full_path)
            
    except Exception as e:
        page.snack_bar = ft.SnackBar(
            ft.Text(f"Error al exportar a Excel: {str(e)}"), 
            bgcolor=ft.colors.RED_700
        )
        page.snack_bar.open = True
        page.update()
