-- 01. Source profiling (SQL Server)
SELECT
    COUNT(*)                                                    AS total_rows,
    COUNT(DISTINCT pedido_id)                                   AS unique_order_ids,
    SUM(CASE WHEN fecha_pedido IS NULL THEN 1 ELSE 0 END)       AS missing_order_dates,
    SUM(CASE WHEN fecha_prometida IS NULL THEN 1 ELSE 0 END)    AS missing_promised_dates,
    SUM(CASE WHEN fecha_entrega IS NULL THEN 1 ELSE 0 END)      AS orders_without_actual_delivery,
    SUM(CASE WHEN unidades_pedidas IS NULL THEN 1 ELSE 0 END)   AS missing_units_ordered,
    SUM(CASE WHEN costo_transporte IS NULL THEN 1 ELSE 0 END)   AS missing_costs,
    SUM(CASE WHEN costo_transporte < 0 THEN 1 ELSE 0 END)       AS negative_costs
FROM dbo.pedidos_logistica;
