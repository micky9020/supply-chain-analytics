# Supply Chain Analytics: calidad de datos, OTIF y costo logistico

Proyecto de analitica de extremo a extremo para una operacion de distribucion con costos de transporte
al alza y entregas tardias o incompletas. Cubre perfilado y limpieza de datos, calculo de **OTIF** y costo
por orden, desempeno por almacen y transportista, y escenarios de impacto financiero, con equivalentes en
**Python, SQL Server y Power BI**.

> **Aviso:** todas las cifras del caso de estudio y los datos de ejemplo son **hipoteticos**. Sirven para
> demostrar el metodo y no representan resultados reales de ninguna empresa.

## Caso de referencia

| Parametro | Supuesto ilustrativo |
|---|---|
| Periodo de analisis | Enero-junio (6 meses) |
| Volumen | 50,000 ordenes |
| Costo logistico | S/ 2,400,000 (S/ 48 por orden) |
| Meta OTIF | 95% (escenario base: 88%) |

El documento completo esta en [`docs/case_study_corrected.pdf`](docs/case_study_corrected.pdf).

## Estructura

```
.
├── run_pipeline.py                # Punto de entrada (CLI)
├── src/supply_chain/
│   ├── config.py                  # Parametros: formato de fecha, corte, mapeos, escenarios
│   ├── cleaning.py                # Normalizacion, banderas de error, excepciones
│   ├── kpis.py                    # OTIF, retrasos, costo por orden, resumenes por segmento
│   ├── financial.py               # Escenarios de ahorro y ROI
│   └── pipeline.py                # Orquestacion y escritura de resultados
├── scripts/generate_sample_data.py  # Datos sinteticos con errores intencionales
├── sql/                           # Controles de calidad y KPI en SQL Server
├── powerbi/                       # Medidas DAX y guia del tablero
├── tests/                         # Pruebas de las reglas de negocio
├── docs/case_study_corrected.pdf  # Caso de estudio revisado
└── data/ , outputs/               # Datos de entrada y resultados (no se versionan)
```

## Inicio rapido

```bash
python -m venv .venv && source .venv/bin/activate    # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/generate_sample_data.py --rows 5000   # o coloca tu CSV en data/raw/
python run_pipeline.py --input data/raw/pedidos_logistica.csv --output-dir outputs
pytest
```

Opciones utiles: `--cutoff 2026-06-30`, `--date-format "%d/%m/%Y"`, `--investment 30000`.

## Que produce el pipeline (`outputs/`)

| Archivo | Contenido |
|---|---|
| `audit.json` | Perfilado crudo y conteo/porcentaje de cada regla de limpieza |
| `clean_valid.csv` | Ordenes elegibles con OTIF, dias de retraso y costo por unidad |
| `exceptions.csv` | Registros observados con el motivo (nada se descarta en silencio) |
| `kpi_monthly.csv`, `kpi_by_warehouse.csv`, `kpi_by_carrier.csv` | OTIF, costo por orden y retraso por segmento |
| `financial_scenarios.csv` | Ahorro bruto, beneficio neto y ROI por escenario |

## Reglas de negocio clave

1. **Solo se eliminan duplicados exactos.** Los IDs repetidos con datos distintos se marcan
   (`error_id_duplicado`) y van a excepciones hasta resolverlos con una regla documentada.
2. **Las anomalias se marcan, no se borran:** cantidades invalidas o en exceso, costos negativos o nulos,
   fechas faltantes o incoherentes (promesa anterior al pedido, entrega anterior al pedido).
3. **Elegibilidad para OTIF:** sin errores, no cancelada y con fecha prometida <= fecha de corte.
   Una orden abierta que **no ha vencido** se excluye; una abierta y **ya vencida** cuenta como fallo.
4. **Periodo mensual = mes prometido**, no el mes de creacion del pedido.
5. **OTIF = entrega completa Y a tiempo** (`unidades_entregadas >= unidades_pedidas` y
   `fecha_entrega <= fecha_prometida`).
6. **Mejora de servicio no es ahorro en efectivo.** Los beneficios financieros se calculan con costos
   verificados (reentregas, penalidades, horas extra, devoluciones, fletes urgentes).

## Escenarios financieros del caso

| Escenario | Reduccion | Ahorro bruto (6 m) | Beneficio neto (inv. S/ 30,000) | ROI |
|---|---|---|---|---|
| Conservador | 3% | S/ 72,000 | S/ 42,000 | 140% |
| Base | 5% | S/ 120,000 | S/ 90,000 | 300% |
| Optimista | 8% | S/ 192,000 | S/ 162,000 | 540% |

Son supuestos, no un pronostico. Con los datos sinteticos de 5,000 filas el costo base es mucho menor, por lo
que hay que escalar la inversion (`--investment`) para que el ROI tenga sentido.

## Limitaciones

- Los cortes por transportista o almacen **no prueban causalidad** (ruta, volumen, tipo de carga y ventanas
  de entrega pueden explicar las diferencias).
- Los alias de transportistas y estados en `config.py` son ejemplos; reemplazalos por la lista real.
- Confirma el grano de la tabla: entregas parciales requieren una tabla a nivel de envio.

## Licencia

MIT. Ver [`LICENSE`](LICENSE).
