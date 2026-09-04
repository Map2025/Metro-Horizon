import flet as ft
import os

class AcercaDeView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.build_ui()

    def cerrar_dialogo(self, dlg):
        dlg.open = False
        self.page.update()

    def abrir_ayuda(self, e):
        ruta_ayuda = os.path.join(os.getcwd(), "Ayuda.md")
        if os.path.exists(ruta_ayuda):
            try:
                with open(ruta_ayuda, "r", encoding="utf-8") as f:
                    md_text = f.read()
                
                dlg = ft.AlertDialog(
                    title=ft.Row([ft.Icon(ft.icons.MENU_BOOK), ft.Text("Manual de Ayuda")]),
                    content=ft.Container(
                        content=ft.Column([
                            ft.Markdown(
                                md_text,
                                selectable=True,
                                extension_set="gitHubWeb",
                            )
                        ], scroll=ft.ScrollMode.AUTO),
                        width=800,
                        height=600,
                        padding=10,
                    ),
                    actions=[
                        ft.TextButton("Cerrar", on_click=lambda e: self.cerrar_dialogo(dlg))
                    ],
                )
                self.page.dialog = dlg
                dlg.open = True
                self.page.update()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"Error al leer el archivo: {ex}"), bgcolor=ft.colors.RED_700
                )
                self.page.snack_bar.open = True
                self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("No se encontró el archivo Ayuda.md en la raíz del proyecto."), 
                bgcolor=ft.colors.RED_700
            )
            self.page.snack_bar.open = True
            self.page.update()

    def build_ui(self):
        self.content = ft.Column(
            [
                ft.Container(height=50), # Espaciador superior
                ft.Icon(ft.icons.ANALYTICS_OUTLINED, size=80, color=ft.colors.BLUE_700),
                ft.Text("Metro Horizon", size=40, weight=ft.FontWeight.BOLD),
                ft.Text("Versión 1.0.0", size=16, color=ft.colors.GREY_600),
                ft.Container(height=20), # Espaciador
                
                ft.Text(
                    "Plataforma de Inteligencia de Negocios y Analítica Financiera\n"
                    "integrada con Tango Software.",
                    text_align=ft.TextAlign.CENTER,
                    size=16
                ),
                
                ft.Container(height=30), # Espaciador
                
                ft.ElevatedButton(
                    "Abrir Manual de Ayuda", 
                    icon=ft.icons.MENU_BOOK, 
                    on_click=self.abrir_ayuda,
                    width=250,
                    height=50
                ),
                
                ft.Container(expand=True), # Empuja el copyright hacia abajo
                
                ft.Divider(),
                ft.Text("© 2026 Serviciosoft - Todos los derechos reservados", size=12, color=ft.colors.GREY_500),
                ft.Container(height=10),
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
