-- 02. Repeated order IDs (investigate: exact copy, corrected version or partial shipment)
SELECT pedido_id, COUNT(*) AS row_count
FROM dbo.pedidos_logistica
GROUP BY pedido_id
HAVING COUNT(*) > 1;
