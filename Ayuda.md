# Metro Horizon - Manual de Usuario y Ayuda

Bienvenido a **Metro Horizon**, la plataforma de Inteligencia de Negocios y Analítica Financiera diseñada para integrarse directamente con el sistema ERP Tango Software. Esta aplicación permite a los gerentes financieros y tesoreros visualizar el estado real de la liquidez, evaluar la eficiencia de cobranzas y predecir riesgos a futuro mediante Inteligencia Artificial.


## 1. Configuración Inicial

Para que la aplicación funcione correctamente, asegúrese de tener configurado el archivo `.env` en la raíz del proyecto con la cadena de conexión a su base de datos de Tango Software.

Ejemplo de configuración en `.env`:
`DB_CONNECTION_STRING="Driver={SQL Server};Server=SU_SERVIDOR;Database=SU_BASE_DE_DATOS;UID=usuario;PWD=contraseña;"`


## 2. Módulos Analíticos
Estos reportes analizan información histórica y actual del sistema para brindarle un estado de situación preciso.

### 2.1. Flujo de Efectivo Real (Tesorería)
Módulo encargado de reconstruir el flujo de caja histórico basado **estrictamente en los movimientos de cuentas de liquidez** (Cajas y Bancos).
* **Cómo usarlo:** Seleccione un rango de fechas utilizando los calendarios y presione *"Generar Flujo Real"*.
* **Características:**
  * Ignora asientos de devengamiento y cheques de terceros en cartera, mostrando solo el "dinero duro".
  * Integra reversiones y anulaciones contables para mostrar el saldo neto real.
  * Haga clic sobre cualquier fila de la tabla inferior para realizar un **Drill-Down** (apertura de datos) y ver los comprobantes y proveedores/clientes que componen ese importe.

### 2.2. Ratio de Ventas vs Cobranzas
Permite evaluar la eficiencia del equipo de cobranzas y la salud financiera de la facturación.
* **Cómo usarlo:** Defina el período a evaluar y presione *"Generar Reporte"*.
* **Características:**
  * Cruza el total facturado bruto (incluye IVA, Notas de Débito y Crédito) contra el total de ingresos recibidos (Recibos al Haber).
  * Genera un Ratio de Eficiencia mensual (%) que se pinta de verde, naranja o rojo según la salud de recaudo.


## 3. Módulos Predictivos
Estos reportes utilizan lógicas algorítmicas y de Machine Learning (Inteligencia Artificial) para proyectar escenarios futuros.

### 3.1. Proyección de Flujo de Caja (Cash Flow)
Calcula cómo estará la liquidez de la empresa en las próximas 4 semanas.
* **Cómo usarlo:** Presione el botón *"Generar Proyección"*.
* **Características:**
  * **Ingresos Proyectados:** Toma la liquidez inicial, suma los cheques de terceros a vencer cada semana, y añade las facturas de deudores ajustadas por su **Probabilidad de Pago** (usando Machine Learning).
  * **Egresos Proyectados:** Toma las fechas de vencimiento de las órdenes de pago (compras a proveedores).
  * **Drill-Down:** Al hacer clic sobre el ícono de la lupa en la columna "Ingresos", podrá ver qué clientes específicos componen el ingreso esperado de esa semana.

### 3.2. Riesgo de Morosidad
Utiliza un algoritmo de clasificación probabilística (Regresión Logística) para auditar toda la cartera de clientes con saldo deudor.
* **Cómo usarlo:** Presione *"Calcular Riesgo / Actualizar Datos"*. Puede filtrar la tabla utilizando el menú desplegable superior.
* **Características:**
  * Analiza el comportamiento histórico del cliente: saldo actual, días de atraso, antigüedad desde la última factura y el último pago.
  * Asigna un **Score (0 a 100%)** y una etiqueta de riesgo (Alto, Medio, Bajo).


## 4. Funcionalidades Comunes y Herramientas

* **Exportación a Excel:** En todos los reportes encontrará un botón para *"Exportar a Excel"*. Al presionarlo, el sistema guardará automáticamente una copia estructurada de los datos en su carpeta local de **Descargas (Downloads)** y abrirá el archivo de inmediato.
* **Modo Claro / Oscuro:** Puede cambiar el tema visual de la aplicación en cualquier momento presionando el ícono de "Luna/Sol" ubicado en la esquina superior derecha de la barra de navegación.


## 5. Soporte Técnico
Si la aplicación no logra conectarse a la base de datos o si experimenta lentitud, verifique su conexión a la red local (LAN) o VPN donde se encuentra alojado el servidor de Tango Software.