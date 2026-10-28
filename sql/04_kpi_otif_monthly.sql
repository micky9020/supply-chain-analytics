-- 04. OTIF and cost per order by PROMISED month (SQL Server)
-- Rules: eligible orders only (promise <= cutoff, not cancelled, no errors, unique ID).
-- An open order already overdue counts as a failure; one not yet due is excluded.
DECLARE @cutoff DATE = '2026-06-30';

WITH unique_ids AS (
    SELECT pedido_id FROM dbo.pedidos_logistica GROUP BY pedido_id HAVING COUNT(*) = 1
),
eligible AS (
    SELECT p.*
    FROM dbo.pedidos_logistica p
    JOIN unique_ids u ON u.pedido_id = p.pedido_id
    WHERE p.fecha_prometida <= @cutoff
      AND UPPER(LTRIM(RTRIM(p.estado))) <> 'CANCELADO'
      AND p.unidades_pedidas > 0
      AND p.unidades_entregadas >= 0 AND p.unidades_entregadas <= p.unidades_pedidas
      AND p.costo_transporte >= 0
      AND p.fecha_pedido IS NOT NULL
      AND p.fecha_prometida >= p.fecha_pedido
      AND (p.fecha_entrega IS NULL OR p.fecha_entrega >= p.fecha_pedido)
      AND (p.unidades_entregadas IS NOT NULL OR p.fecha_entrega IS NULL)
)
SELECT
    FORMAT(fecha_prometida, 'yyyy-MM')                          AS mes,
    COUNT(*)                                                    AS orders,
    SUM(costo_transporte)                                       AS total_cost,
    SUM(costo_transporte) * 1.0 / COUNT(*)                      AS cost_per_order,
    100.0 * SUM(CASE WHEN fecha_entrega IS NOT NULL
                      AND fecha_entrega <= fecha_prometida
                      AND unidades_entregadas >= unidades_pedidas
                     THEN 1 ELSE 0 END) / COUNT(*)              AS otif_pct
FROM eligible
GROUP BY FORMAT(fecha_prometida, 'yyyy-MM')
ORDER BY mes;
