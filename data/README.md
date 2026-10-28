# Datos

Esta carpeta **no versiona datos**. Coloca tu archivo en `data/raw/pedidos_logistica.csv` o genera datos
sinteticos con:

```bash
python scripts/generate_sample_data.py --rows 5000
```

Columnas esperadas: `pedido_id, fecha_pedido, fecha_prometida, fecha_entrega, almacen, transportista,
unidades_pedidas, unidades_entregadas, costo_transporte, estado`.
