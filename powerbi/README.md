# Power BI

Importa a Power BI Desktop los CSV generados en `outputs/` (`clean_valid.csv` como tabla `Pedidos`,
`kpi_*.csv` y `financial_scenarios.csv` como tablas de apoyo) y crea una tabla `Calendario` relacionada
con `fecha_prometida`. Las medidas estan en [`measures.dax`](measures.dax).

| Pagina | Contenido | Pregunta de gestion |
|---|---|---|
| 1. Resumen ejecutivo | OTIF vs meta, costo total, costo por orden, tendencia mensual | Servicio y costo van segun lo previsto? |
| 2. Desempeno operativo | Almacen, transportista y ruta; retrasos; costo por orden/unidad | Donde se concentran las fallas? |
| 3. Impacto financiero | Ahorro potencial vs realizado; escenarios; ROI | Que acciones crean valor medible? |

Antes de publicar, valida los totales del tablero contra la salida aprobada de SQL o Python.
